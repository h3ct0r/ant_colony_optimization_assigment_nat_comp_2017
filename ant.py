import random
import time
from threading import Thread
import math
import numpy as np

class Ant(Thread):
    def __init__(self, ant_id, alpha, beta, data, ant_pheromone_map, pheromone_map, density_map, p_count):
        super(Ant, self).__init__()

        self.ant_id = ant_id
        self.alpha = alpha
        self.beta = beta
        self.data = data
        self.ant_pheromone_map = ant_pheromone_map
        self.pheromone_map = pheromone_map
        self.density_map = density_map
        self.p_count = p_count

        self.previous_result = None
        self.previous_result_status = False
        self.previous_result_sum = float("inf")

    def run(self):
        self.select_p_medians()

    def select_p_medians(self):
        p_medians = []
        node_indexes = [n.node_id for n in self.data]

        node_fitness = []
        for n in self.data:
            node_i = n.node_id
            p_v1 = (self.pheromone_map[node_i] ** self.alpha) * (self.density_map[node_i] ** self.beta)
            p_v2 = sum([((self.pheromone_map[i] ** self.alpha) * (self.density_map[i] ** self.beta)) for i in xrange(len(self.pheromone_map))])
            p_k_i = float(p_v1) / float(p_v2)
            node_fitness.append(p_k_i)

        t_start = time.time()
        while len(p_medians) < self.p_count:
            # choose random between (0, 1] and test with eq 10
            closest_i = self._weighted_random_choice(node_fitness)
            #print '[DEBUG]', 'p', p, 'closest_i', closest_i
            if closest_i not in p_medians:
                p_medians.append(closest_i)

        t_end = time.time()
        #print '[TIME 1]', 'elapsed time:{}'.format(t_end - t_start)

        # t_start = time.time()
        # while len(p_medians) < self.p_count:
        #     # random selected node
        #     next_node_i = random.choice(node_indexes)
        #     if next_node_i in p_medians:
        #         continue
        #
        #     # calculate prob by eq 10
        #     p_v1 = (self.pheromone_map[next_node_i] ** self.alpha) * (self.density_map[next_node_i] ** self.beta)
        #     p_v2 = sum([((self.pheromone_map[i] ** self.alpha) * (self.density_map[i] ** self.beta)) for i in xrange(len(self.pheromone_map))])
        #     p_k_i = float(p_v1) / float(p_v2)
        #
        #     # choose random between (0, 1] and test with eq 10
        #     p = random.random()
        #     if p <= p_k_i:
        #         p_medians.append(next_node_i)
        # t_end = time.time()
        #print '[TIME 1]', 'elapsed time:{}'.format(t_end - t_start)


        return self.calculate_result(p_medians)

    def calculate_result(self, p_medians):
        print '[DEBUG]', 'Ant {} choosing p-medians: {}'.format(self.ant_id, p_medians)

        allocations = dict()
        allocated_nodes = []
        allocation_sum = 0
        t_start = time.time()
        for median_i in p_medians:
            median_node = self.data[median_i]
            x1 = median_node.x
            y1 = median_node.y

            l = list(sorted(self.data, key=lambda (a): (a.x - x1) ** 2 + (a.y - y1) ** 2))
            il = []
            for e in l:
                if e.node_id not in allocated_nodes and e.node_id not in p_medians:
                    il.append(e.node_id)

            #print 'l:{}'.format(l)
            #print 'p_medians:{}'.format(p_medians)
            #print 'il:{} {}'.format(len(il), il)

            local_alloc = []
            c_capacity = median_node.c
            sum_distance = 0
            for j in il:
                n = self.data[j]
                if c_capacity <= 0:
                    break

                #print 'c_capacity:', c_capacity, n.d

                if n.d <= c_capacity:
                    c_capacity -= n.d
                    local_alloc.append(n.node_id)
                    sum_distance += math.sqrt((n.x - x1) ** 2 + (n.y - y1) ** 2)

            allocated_nodes = allocated_nodes + local_alloc
            allocation_sum += sum_distance
            allocations[median_i] = {'sum_distance': sum_distance, 'nodes': local_alloc}

        t_end = time.time()
        #print '[TIME 2]', 'elapsed time:{}'.format(t_end - t_start)


        #print 'allocated_nodes:{}'.format(allocated_nodes)
        #print '[DEBUG]', 'Ant {} allocations {}'.format(self.ant_id, allocations)
        self.previous_result = allocations

        if len(allocated_nodes) != len(self.data) - len(p_medians):
            self.previous_result_status = False
        else:
            self.previous_result_status = True

        self.previous_result_sum = allocation_sum

        #print '[DEBUG]', 'Ant {} result is valid? {} {}/{}'.format(self.ant_id, self.previous_result_status, len(allocated_nodes), len(self.data) - len(p_medians))
        return self.previous_result_status

    @staticmethod
    def _weighted_random_choice(fitness_l):
        max_f = sum(fit for fit in fitness_l)
        pick = random.uniform(0, max_f)
        current = 0
        for i in xrange(len(fitness_l)):
            fit = fitness_l[i]
            current += fit
            if current > pick:
                return i
