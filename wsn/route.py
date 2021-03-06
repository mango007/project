#this module generates routing tables
from sqlwsn import DatabaseAccess
import random
import sys
import operator
import math
import setting

class Route():
    def __init__(self,exp):
        self.dba = DatabaseAccess()
        self.cc = setting.cc*setting.rt/60
        self.cst = setting.cst
        self.csr = setting.csr
        self.clc = setting.clc*setting.rt/60
        self.clt = setting.clt
        self.r = setting.r*setting.rt/60
        self.exp = exp


    # def getRandomRouting(self,routingRound):
    #     table = {}
    #     random.seed(routingRound)
    #     choosenNumOfBss = random.randint(1,len(self.dba.baseStations.keys()))
    #     baseStations = random.sample(self.dba.baseStations.keys(),choosenNumOfBss)
    #     #record visited nodes, initially including all base stations
    #     visited = []
    #     visited.extend(baseStations)
    #
    #     #record nodes which have unvisited neighbors
    #     hasUnvisitedNb = [baseStation for baseStation in baseStations if len(self.getNeighbors(baseStation, visited)) != 0]
    #
    #     numOfSensors = len(self.dba.sensors)
    #     while len(visited) != numOfSensors:
    #         try:
    #             node = random.choice(hasUnvisitedNb)
    #             nbs = self.getNeighbors(node, visited)
    #             if len(nbs) == 0:
    #                 hasUnvisitedNb.remove(node)
    #                 continue
    #
    #             choosenNumOfNbs = random.randint(0,len(nbs))
    #             choosenNbs = random.sample(nbs, choosenNumOfNbs)
    #             visited.extend(choosenNbs)
    #             if len(choosenNbs) == len(nbs):
    #                 hasUnvisitedNb.remove(node)
    #
    #             for sensor in choosenNbs:
    #                 table[sensor] = node
    #                 nbs = self.getNeighbors(sensor, visited)
    #                 if len(nbs) != 0:
    #                     hasUnvisitedNb.append(sensor)
    #         except:
    #             print "some sensor can not connect to base station"
    #             sys.exit()
    #     F0 = [i for i in baseStations if i in table.values() and i not in table.keys()]
    #     return (table,F0)

    def getRandomRouting(self,routingRound):
        visited = {}
        unvisited = {}
        infinity = float("inf")
        F0 = []

        #Calculate lambda and calculate the distance between sensors
        (lamb, d) = self.getLambdaAndDistance(routingRound)

        for s in self.dba.sensors.keys():
            unvisited[s] = (infinity, None)

        #randomly choose active base stations
        random.seed(routingRound)
        choosenNumOfBss = random.randint(1,len(self.dba.baseStations.keys()))
        baseStations = random.sample(self.dba.baseStations.keys(),choosenNumOfBss)
        for bs in baseStations:
            unvisited[bs] = (0, None)
        F0.extend(baseStations)
        table = self.shortestPath1(d, visited, unvisited)
        return (table,F0)

    def getShortestPathRouting(self, routingRound, useAllBasestation = True, numOfBasestations = 1):
        visited = {}
        unvisited = {}
        infinity = float("inf")
        F0 = []

        #Calculate lambda and calculate the distance between sensors
        (lamb, d) = self.getLambdaAndDistance(routingRound)

        if useAllBasestation:
            for rs in self.dba.regularSensors.keys():
                unvisited[rs] = (infinity, None)
            for bs in self.dba.baseStations.keys():
                unvisited[bs] = (0, None)
            F0.extend([i for i in self.dba.baseStations.keys()])
        else:
            for s in self.dba.sensors.keys():
                unvisited[s] = (infinity, None)
            baseStations = self.dba.baseStations.keys()[0:numOfBasestations]
            for bs in baseStations:
                unvisited[bs] = (0, None)
            F0.extend(baseStations)

        table = self.shortestPath1(d, visited, unvisited)
        return (table,F0)

    def nbs(self, currId, unvisited, d):
        return [e for e in d[currId].keys() if e in unvisited]

    #For all sensors, calculate the shortest routing path to one of the base stations
    def shortestPath1(self,d,visited,unvisited):
        table = {}
        while unvisited.keys():
            minNode = min(unvisited, key=unvisited.get)
            visited[minNode] = (unvisited[minNode][0], unvisited[minNode][1])
            del unvisited[minNode]
            nbs = self.nbs(minNode, unvisited.keys(),d)
            for nb in nbs:
                if nb in unvisited.keys() and visited[minNode][0]+d[minNode][nb] < unvisited[nb][0]:
                    unvisited[nb] = (visited[minNode][0]+d[minNode][nb], minNode)
        for t in visited.keys():
            if visited[t][1] is not None:
                table[t] = visited[t][1]
        return table

    def getMovingBaseStationRouting(self,routingRound):
        #Calculate lambda and calculate the distance between sensors
        (lamb, d) = self.getLambdaAndDistance(routingRound)
        (table,F0) = self.minWeight(self.cc,self.cst,self.csr,self.clc,self.clt,self.r,lamb,d)
        return (table,F0)

    def getLambda(self,routingRound):
        e = self.dba.getRemianingEnergy()
        initEnergy = {}
        theta = {}
        alpha = setting.alpha

        for bs in self.dba.baseStations.keys():
            theta[bs] = None
            initEnergy[bs] = self.dba.baseStations[bs].initialEnergy
        for rs in self.dba.regularSensors.keys():
            theta[rs] = None
            initEnergy[rs] = self.dba.regularSensors[rs].initialEnergy
        #Calculate theta
        if routingRound == 0:
            for i in theta.keys():
                theta[i] = 0
        else:
            for i in theta.keys():
                theta[i] = (initEnergy[i]-e[i])/(routingRound)

        lamb = {}
        tmp = 0
        for i in theta.keys():
            lamb[i] = math.exp(alpha*theta[i]/initEnergy[i])
            tmp += lamb[i]
        for i in theta.keys():
            lamb[i] = lamb[i]/(initEnergy[i]*tmp)
        return lamb

    def getLambdaAndDistance(self, routingRound):
        #Calculate lambda
        lamb = self.getLambda(routingRound)

        #calculate the distance between sensors
        d = {}
        d['s'] = {}
        nb = self.dba.neighborhood
        infinity = float("inf")
        for i in nb.keys():
            d[i] = {}
            if i in self.dba.baseStations.keys():
                d['s'][i] = infinity
                d[i]['s'] = lamb[i]*self.clt*self.r
            for j in nb[i].keys():
                d[i][j] = lamb[i]*self.cst*self.r+lamb[j]*self.csr*self.r

        return (lamb, d)

    def minWeight(self,cc,cst,csr,clc,clt,r,lamb,d):
        table = {}
        F0 = []

        F = self.dba.baseStations.keys()
        C = self.dba.regularSensors.keys()
        L = self.shortestPath2(d,F,C)

        g = {}
        h = {}
        for u in F:
            h[u] = lamb[u]*clc
            g[u] = {}
            for v in C:
                g[u][v] = L[u][v][0]+lamb[v]*cc

        Cu = [j for j in C]

        while Cu:
            bestStar = self.getMostCostEffectiveStar(F,F0,C,Cu,g,h)
            if bestStar is None:
                print 'error'
                sys.exit()
            else:
                (i,D) = bestStar

                if i in table.keys():
                    del table[i]
                for j in D:

                    table[j] = L[i][j][1]

                    #if the next node is a base station except i
                    if table[j] in F and table[j] != i:
                        table[table[j]] = L[i][table[j]][1]
                    if j in Cu:
                        Cu.remove(j)
                F0.append(i)
        for i in F0:
            if i in table.keys():
                del table[i]
        # cost = self.getRealCost(F0,F,C,table,cc,cst,csr,clc,clt,r)
        return (table,F0)

    #For each base station, calculate the shortest routing table for other nodes
    def shortestPath2(self,d,F,C):
        L = {}
        infinity = float("inf")

        for bs in F:
            visited = {}
            unvisited = {}
            L[bs] = {}
            unvisited[bs] = (0, None)
            #add all the regular sensors into the unvisited set
            for rs in C:
                unvisited[rs] = (infinity, None)
            # add all the other base stations into the unvisited set
            for b in F:
                if b != bs:
                    unvisited[b] = (infinity, None)

            while unvisited.keys():
                minNode = min(unvisited, key=unvisited.get)
                visited[minNode] = (unvisited[minNode][0], unvisited[minNode][1])
                del unvisited[minNode]
                nbs = self.nbs(minNode, unvisited.keys(), d)
                for nb in nbs:
                    if visited[minNode][0]+d[minNode][nb] < unvisited[nb][0]:
                        unvisited[nb] = (visited[minNode][0]+d[minNode][nb], minNode)
            #add cost for communicating with remote server
            for t in visited.keys():
                if t != bs:
                    L[bs][t] = (visited[t][0]+d[bs]['s'],visited[t][1])
        return L



    def getMostCostEffectiveStar(self,F,F0,C,Cu,g,h):
        minCost = float("inf")
        bestStar = None
        for i in F:
            if i not in F0:
                tmp = {}
                for j in Cu:
                    tmp[j] = g[i][j]
                tmp = sorted(tmp.items(), key=operator.itemgetter(1))
                sortedCu = [ele[0] for ele in tmp]
                Cc = []
                for j in C:
                    if j not in Cu:
                        if self.getQC(i,j,g,F0) < 0:
                            Cc.append(j)
                for k in range(1,len(sortedCu)+1):
                    D = []
                    D.extend(Cc)
                    for j in sortedCu[0:k]:
                        D.append(j)
                    cost = self.getCost(i,k,D,g,h,F0,Cu)
                    if cost < minCost:
                        minCost = cost
                        bestStar = (i, D)
        return bestStar

    def getQU(self,i,j,g):
        return g[i][j]

    def getQC(self,i,j,g,F0):
        tmp = float("inf")
        for k in F0:
            if g[k][j] < tmp:
                tmp = g[k][j]
        return min(0,g[i][j]-tmp)


    def getQ(self,i,j,g,F0,Cu):
        if j in Cu:
            return self.getQU(i,j,g)
        else:
            return self.getQC(i,j,g,F0)

    def getCost(self,i,k,D,g,h,F0,Cu):
        tmp = 0
        for j in D:
            tmp += self.getQ(i,j,g,F0,Cu)
        return (h[i]+tmp)/k

    # def getRealCost(self,F0,F,C,table,cc,cst,csr,clc,clt,r):
    #     tablecopy = {}
    #     for i in table.keys():
    #         tablecopy[i] = table[i]
    #     datain = {}
    #     dataout = {}
    #     for i in C:
    #         datain[i] = 0
    #         dataout[i] = 0
    #     for i in F:
    #         datain[i] = 0
    #         dataout[i] = 0
    #
    #     while tablecopy:
    #         nodes = tablecopy.keys()
    #         nextNodes = tablecopy.values()
    #         leaf = [i for i in nodes if i not in nextNodes]
    #         for i in leaf:
    #             if tablecopy[i] is not None:
    #                 dataout[i] = datain[i]+r
    #                 datain[tablecopy[i]] += dataout[i]
    #                 del tablecopy[i]
    #     cost = {}
    #     for i in F:
    #         if i not in F0:
    #             cost[i] = cc+cst*dataout[i]+csr*datain[i]
    #         else:
    #             cost[i] = cc+cst*dataout[i]+csr*datain[i]+clc+clt*(datain[i]-dataout[i])
    #     for i in C:
    #         cost[i] = cc+cst*dataout[i]+csr*datain[i]
    #     return cost

    #get routing table and activated time of each base station
    def getRoutingTable(self, routingRound):
        m = ''

        #if other routing approaches are added, this part should be modified
        if self.exp == 0:
            (table,F0) = self.getRandomRouting(routingRound)
        elif self.exp == 1:
            (table,F0) = self.getShortestPathRouting(routingRound,useAllBasestation=False, numOfBasestations=1)
        elif self.exp == 2:
            (table,F0) = self.getShortestPathRouting(routingRound,useAllBasestation=True)
        else:
            (table,F0) = self.getMovingBaseStationRouting(routingRound)

        if table is None:
            print "getRoutingTable error"
            sys.exit()

        #insert information about activated base stations into ActiveBS table
        self.dba.insertActive(self.exp,routingRound,F0)

        #the format od returned routing message is [Node:NextNode,],e.g. "1:2,2:3"
        for i in table.keys():
            m += chr(i)+':'+chr(table[i])+','
        return m

# if __name__ == "__main__":
#     route = Route(3)
#     # (table,F0) = route.getRandomRouting()
#     # for e in table:
#     #     print e,":",table[e]
#     # print "---------------------------"
#     # table = route.getShortestPathRouting(useAllBasestation=False, numOfBasestations=1)
#     # print "OneBasestationShortestPathRouting"
#     # for e in table:
#     #     print e,":",table[e]
#     # print "---------------------------"
#     # table = route.getRandomRouting()
#     # print "RandomRouting"
#     # for e in table:
#     #     print e,":",table[e]
#     # print "---------------------------"
#     #
#
#
#     print len(route.configMBSR)

