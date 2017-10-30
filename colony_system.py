import csv
import os
import random
from ant import Ant


class Node(object):
    def __init__(self, node_id, x, y, c, d):
        self.node_id = node_id
        self.x = x
        self.y = y
        self.c = c
        self.current_c = c
        self.d = d

    def get_id(self):
        return self.node_id

    def get_pos(self):
        return self.x, self.y

    def get_total_capacity(self):
        return self.c

    def get_capacity(self):
        return self.current_c

    def get_demand(self):
        return self.d

    def add_demand(self, d):
        if d <= self.current_c:
            self.current_c -= d
            return True
        else:
            return False


class ColonySystem(object):
    def __init__(self, cfg):
        self.cfg = cfg
        self.node_count = 0
        self.p_count = 0

        self.ant_number = self.cfg["ant_number"]
        self.alpha = self.cfg["alpha"]
        self.beta = self.cfg["beta"]
        self.pheromone_evaporation = self.cfg["pheromone_evaporation"]
        self.pheromone_t0 = self.cfg["pheromone_t0"]
        self.iterations = self.cfg["iterations"]

        self.data = []
        self.read_database()

        self.pheromone_map = [self.pheromone_t0 for i in xrange(len(self.data))]
        self.ant_pheromone_map = [0.000000001 for i in xrange(len(self.data))]
        self.density_map = self.calculate_density_map()

        print '[INFO]', 'Density map\n', self.density_map

        random.seed(self.cfg["seed"])

        self.global_best_sum = float("inf")
        self.global_best_p_medians = []
        self.global_best = None

        pass

    def start(self):
        # define ants
        print '[INFO]', 'Creating {} ants'.format(self.ant_number)
        ants = []
        for i in xrange(self.ant_number):
            ants.append(Ant(i, self.alpha, self.beta, self.data, self.ant_pheromone_map, self.pheromone_map, self.density_map, self.p_count))

        for it in xrange(self.iterations):
            print '[INFO]', 'Iteration {}'.format(it)

            for ant_i in xrange(self.ant_number):
                ant = ants[ant_i]
                ant.start()

            for ant_i in xrange(self.ant_number):
                ant = ants[ant_i]
                ant.join()

            l = sorted(ants, key=lambda (a): a.previous_result_sum)
            best_ant = l[0]
            worst_ant = l[-1]

            if best_ant.previous_result_sum < self.global_best_sum:
                self.global_best_sum = best_ant.previous_result_sum
                self.global_best_p_medians = best_ant.previous_result.keys()
                self.global_best = best_ant.previous_result
                print '[DEBUG]', 'Updated global best to {}'.format(self.global_best_sum)

            for k in best_ant.previous_result.keys():
                # print 'a', (best_ant.previous_result_sum - self.global_best_sum)
                # print 'b', float(worst_ant.previous_result_sum)
                # print 'c', best_ant.previous_result_sum
                self.ant_pheromone_map[k] = 1 - ((best_ant.previous_result_sum - self.global_best_sum)/float(worst_ant.previous_result_sum - best_ant.previous_result_sum))

            print '[DEBUG]', 'Best ant ID:{} Sum:{}'.format(best_ant.ant_id, best_ant.previous_result_sum)
            print '[DEBUG]', 'Worst ant ID:{} Sum:{}'.format(worst_ant.ant_id, worst_ant.previous_result_sum)
            print '[DEBUG]', 'Global best Sum:{}'.format(self.global_best_sum)

            self.update_pheromone_map()
            #self.print_pheromone_map()
            self.ant_pheromone_map = [0.000000001 for i in xrange(len(self.data))]

            # restart ants because of threads
            for ant_i in xrange(self.ant_number):
                ant = ants[ant_i]

                ant.__init__(ant.ant_id, ant.alpha, ant.beta, ant.data, ant.ant_pheromone_map, ant.pheromone_map, ant.density_map, ant.p_count)
            pass

        print '[INFO]', 'Best solution:{} {}'.format(self.global_best_sum, self.global_best)
        self.show_network_graph(self.global_best)

    def calculate_density_map(self):
        density_map = []
        for i in xrange(len(self.data)):
            c_node = self.data[i]
            x1 = c_node.x
            y1 = c_node.y
            l = list(sorted(self.data, key=lambda (a): (a.x - x1) ** 2 + (a.y - y1) ** 2))

            c_capacity = c_node.c
            allocated_nodes = 0
            sum_distance = 0
            for n in l:
                if n.node_id == c_node.node_id:
                    continue

                if c_capacity <= 0:
                    break

                if n.d <= c_capacity:
                    c_capacity -= n.d
                    allocated_nodes += 1
                    sum_distance += ((n.x - x1) ** 2 + (n.y - y1) ** 2)

            ni = float(allocated_nodes) / float(sum_distance)
            density_map.append(ni)
            pass

        return density_map

    def update_pheromone_map(self):
        t_max = (1.0/(1.0 - self.pheromone_evaporation)) * (1.0/float(self.global_best_sum))
        t_min = t_max / float(2 * len(self.data))

        print '[DEBUG]', 't_max:{} t_min:{}'.format(t_max, t_min)

        for i in xrange(len(self.pheromone_map)):
            self.pheromone_map[i] = (self.pheromone_evaporation * self.pheromone_map[i]) + self.ant_pheromone_map[i]
        pass

    def print_pheromone_map(self):
        print self.ant_pheromone_map
        print self.pheromone_map

    def show_network_graph(self, allocations):
        import networkx as nx
        from matplotlib import pyplot as plt

        G = nx.Graph()
        for k, v in allocations.items():
            nk = self.data[k]
            G.add_node(nk.node_id, posxy=(nk.x, nk.y))
            for e in v['nodes']:
                ne = self.data[e]
                G.add_node(ne.node_id, posxy=(ne.x, ne.y))
                G.add_edge(nk.node_id, ne.node_id)

        color_vals = [(0, 0, 1) if e.node_id in allocations.keys() else (1, 0, 0) for e in self.data]

        positions = nx.get_node_attributes(G, 'posxy')
        nx.draw(G, positions, node_size=len(self.data), node_color=color_vals)
        plt.show()

    def read_database(self):
        if self.cfg['dataset'] is None or not os.path.exists(self.cfg['dataset']):
            raise ValueError('Config file not found {}'.format(self.cfg['dataset']))

        with open(os.path.realpath(self.cfg['dataset']), "r") as f:
            l_count = -1
            for line in f:
                l_count += 1
                d = map(int, line.split())

                if l_count == 0:
                    self.node_count = d[0]
                    self.p_count = d[1]
                    continue
                else:
                    self.data.append(Node(l_count - 1, d[0], d[1], d[2], d[3]))

        print '[INFO]', 'Readed {} nodes from dataset'.format(len(self.data))
        print '[INFO]', 'Dataset has {} p-medians'.format(self.p_count)
