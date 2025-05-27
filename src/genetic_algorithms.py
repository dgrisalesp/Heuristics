from deap import base,creator, tools, algorithms
from base import Data, log_results
import random, math, pandas as pd, sys, argparse
import time



def evaluate(individual):
    orders=[data.orders[i] for i in individual]
    zones, _ = data.calculate_zones_time(orders, data.time_positions, data.order_sku_time, data.s)
    score = data.score_solution(zones)
    return score,

def run_ga(n_generations=100, population_size=50, cxpb=0.5, mutpb=0.2):
    pop= toolbox.population(n=population_size)
    
    hof= tools.HallOfFame(1)
    algorithms.eaSimple(pop, toolbox, cxpb=cxpb, mutpb=mutpb, ngen=n_generations,
                        stats=None, halloffame=hof, verbose=False)
    
    return hof[0]


if __name__ == "__main__":
    parser=argparse.ArgumentParser(description="Orders distribution")
    parser.add_argument('input_file', type=str, help='Input file', default=None)
    parser.add_argument('output_file', type=str, help='Output file [optional]', default=None, nargs='?')
    
    args=parser.parse_args()
    if args.input_file: input_file=args.input_file
    else:
        print('Please provide an input file')
        exit()
    if args.output_file:
        output_file=args.output_file
    else:
        output_file=f'ga_{input_file}'
    
    archive_name=f"../data/{input_file}"
    start_time = time.time()
    data= Data(archive_name)
    creator.create("FitnessMin", base.Fitness, weights=(-1.0,))
    creator.create("Individual", list, fitness=creator.FitnessMin)
    toolbox= base.Toolbox()
    toolbox.register("indices", random.sample, range(len(data.orders)), len(data.orders))
    toolbox.register("individual", tools.initIterate, creator.Individual, toolbox.indices)
    toolbox.register("population", tools.initRepeat, list, toolbox.individual)
    toolbox.register("mutate", tools.mutShuffleIndexes, indpb=0.1)
    toolbox.register("mate", tools.cxOrdered)
    toolbox.register("evaluate", evaluate)
    toolbox.register("select", tools.selTournament, tournsize=3)
    best_individual= run_ga(n_generations=100, population_size=50, cxpb=0.5, mutpb=0.2)
    # print("Best individual: ", best_individual)
    # print("Something good happened")
    best_orders = [data.orders[i] for i in best_individual]
    dict_zones, dict_positions_orders= data.calculate_zones_time(best_orders, data.time_positions, data.order_sku_time, data.s)
    # print("Best solution: ", dict_positions_orders)
    # print("Best zones: ", dict_zones)
    # print(  len(dict_positions_orders.values())-len(set(dict_positions_orders.values())) )
    # print(  len(dict_positions_orders.keys())==len(set(dict_positions_orders.keys())) )
    # print(len(data.orders))
    # print(len(set(dict_positions_orders.values()))==len(set(data.orders)))
    score,= evaluate(best_individual)
    print("Best score: ", score)
    data.write_excel(dict_positions_orders, data.zones_productivity, output_file, input_file)
    print("Execution time:", time.time() - start_time)