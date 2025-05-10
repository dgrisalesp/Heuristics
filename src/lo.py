from base import Data
import random, math, pandas as pd, sys, argparse
import time
from base import Data, log_results

def swap_values(data:Data,orders, dict_zones, dict_positions_oders, idx1, idx2, stop):
    # Swap the values in the orders list
    orders[idx1], orders[idx2] = orders[idx2], orders[idx1]
    
    # Update the zones and positions dictionaries accordingly
    dict_zones[data.time_positions[idx1][0]] -= data.order_sku_time[orders[idx1]] + 2 * data.s[data.time_positions[idx1]]
    dict_zones[data.time_positions[idx2][0]] -= data.order_sku_time[orders[idx2]] + 2 * data.s[data.time_positions[idx2]]
    dict_positions_oders[data.time_positions[idx1][1]], dict_positions_oders[data.time_positions[idx2][1]]=orders[idx1], orders[idx2]
    
    dict_zones[data.time_positions[idx1][0]] += data.order_sku_time[orders[idx1]] + 2 * data.s[data.time_positions[idx1]]
    dict_zones[data.time_positions[idx2][0]] += data.order_sku_time[orders[idx2]] + 2 * data.s[data.time_positions[idx2]]
    
    
    return orders, dict_zones, dict_positions_oders
def first_solution(orders):
    random.shuffle(orders)
    return orders

def local_optimum(data:Data, orders):
    solution=first_solution(orders)
    dict_zones, dict_positions_order = data.calculate_zones_time(solution, data.time_positions, data.order_sku_time, data.s)
    best_max_time = data.score_solution(dict_zones)
    best_solution = solution.copy()
    best_zones = dict_zones.copy()
    best_positions_order = dict_positions_order.copy()
    better_max_time = best_max_time
    better_solution = solution.copy()
    better_zones = dict_zones.copy()
    better_positions_order = dict_positions_order.copy()
    for i in range(100):
        stop=100
        betters=0
        while stop>0 and betters<10:
            idx1, idx2 = random.sample(range(len(solution)), 2)
            
            new_orders, new_dict_zones, new_dict_positions_order = swap_values(data,solution, dict_zones, dict_positions_order, idx1, idx2, stop)
            new_max_time = data.score_solution(new_dict_zones)
            if new_max_time < better_max_time:
                betters+=1
                better_max_time = new_max_time
                better_positions_order= new_dict_positions_order.copy()
                better_zones = new_dict_zones.copy()
                better_solution= new_orders.copy()
            stop-=1
        if better_max_time < best_max_time:
            best_max_time = better_max_time
            best_solution = better_solution.copy()
            best_zones = better_zones.copy()
            best_positions_order = better_positions_order.copy()
            
        solution= best_solution.copy()
        dict_zones= best_zones.copy()
        dict_positions_order= best_positions_order.copy()
        
    return solution, dict_zones, dict_positions_order
                




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
        output_file=f'lo_output_{input_file}'
    
    archive_name=f"../data/{input_file}"

    start_time = time.time()
    data= Data(archive_name)
    solution, dict_zones, dict_positions_order= local_optimum(data, data.orders)
    best_max_time = data.score_solution(dict_zones)
    print("Best max time:", best_max_time)
    print(data.productivity)
    print("Time: ", time.time() - start_time)
    log_results(archive_name, best_max_time, data.zones_productivity, time.time()-start_time, "Local Optimum")
