import os, sys, requests, json, random
sys.path.append(os.path.abspath(os.path.dirname(__file__) + '/..'))
from bson import ObjectId
from collector.device_snmp_collector import DeviceSNMPCollector
from datetime import datetime, timedelta
from device_controller import DeviceController
from elasticsearch import Elasticsearch
from elasticquery import ElasticQuery, Aggregate, Query

class IntellegentLog:
    def __init__(self, db_construct, logger):
        self.db = db_construct
        self.logger = logger

    def format_results(self, results):
        device_controller = DeviceController(self.db, self.logger)
        device_map = device_controller.get_device_map_ip_hostname()
        location_map = device_controller.get_location_map_ip_location()
        """Print results nicely: doc_id) content"""
        query_result= []
        data = [doc for doc in results['hits']['hits']]
        # print data
        for doc in data:
            # self.logger.info(doc["_source"])
            data = {}
            data["severity_label"] = doc["_source"]["severity_label"]
            data["severity"] = doc["_source"]["severity"]
            data["timestamp"] = doc["_source"]["@timestamp"]
            data["host"] = doc["_source"]["host"]
            data["type"] = doc["_source"]["type"]
            data["message"] = doc["_source"]["message"]
            data["hostname"] = device_map[doc["_source"]["host"]]
            data["location"] = location_map[doc["_source"]["host"]]
            query_result.append(data)
        return query_result

    def search(self, parms):
        device_controller = DeviceController(self.db, self.logger)

        if "location" in parms.keys():
            list_location_ip = device_controller.get_device_list_by_locationid(parms["location"])

        if "device" in parms.keys():
            list_device_ip = device_controller.get_device_list_by_hostname(parms["device"])

        #Doing intersection between device search and device in location
        search_ip = list(set(list_location_ip) & set(list_device_ip))
        print search_ip
        query_search = []
        if search_ip:
            query_search.append(Query.terms('host', search_ip))

            if parms["time"]:
                time_from = parms["time"]["from"].split(" ")[0]
                time_to = parms["time"]["to"].split(" ")[0]
                query_search.append(Query.range('@timestamp', gte=time_from, lte=time_to))

            if parms["severityLevel"]:
                query_search.append(Query.terms('severity', parms["severityLevel"]))

            if parms["keywordMessage"]:
                message_search = []
                message_search.append(parms["keywordMessage"])
                query_search.append(Query.terms('message', message_search))

            index = "syslog*"
            es = Elasticsearch(["http://192.168.100.249:9200"])
            q = ElasticQuery(es=es, index=index, doc_type='doc')

            # q.query(Query.match_all())
            q.size(1000)
            q.query(Query.bool(must=query_search))
            #q.query(Aggregate.terms(must=query_search))

            print q.json(indent=4)
            query_result = self.format_results(q.get())
            return query_result
        #No index to query
        else:
            return []

        # message = "*"+parms["keywordMessage"]+"*"
        # query_search.append(Query.wildcard('message', message))

        # all_index = 'http://192.168.100.249:9200/_aliases?pretty=true'
        # headers = {'Content-Type': 'application/json'}
        # response = requests.get(all_index, headers=headers)
        # results = json.loads(response.text)

        # index_ip = [ip for ip in search_ip if ip in results.keys()]
        # IF any index to query
        # if index_ip:
        # print index_ip
        # index = ",".join(index_ip)


        # uri_search = 'http://192.168.100.249:9200/'+index+'/doc/_search'
        # """Simple Elasticsearch Query"""
        # query = json.dumps({
        #     "query": {
        #         # "match": {"message": string_search}
        #         "match_all": {}
        #     }
        # })
        #
        # response = requests.get(uri_search, headers=headers, data=query)
        # results = json.loads(response.text)
        # query_result = self.format_results(results)
