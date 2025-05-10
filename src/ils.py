from base import Data, log_results
import random, math, pandas as pd, sys, argparse
import time
def randomized_construction(data):
    random.shuffle(data)
    return data

def swap_values(data:Data,orders, dict_zones, dict_positions_oders, idx1, idx2):
    # Swap the values in the orders list
    orders[idx1], orders[idx2] = orders[idx2], orders[idx1]
    
    # Update the zones and positions dictionaries accordingly
    dict_zones[data.time_positions[idx1][0]] -= data.order_sku_time[orders[idx1]] + 2 * data.s[data.time_positions[idx1]]
    dict_zones[data.time_positions[idx2][0]] -= data.order_sku_time[orders[idx2]] + 2 * data.s[data.time_positions[idx2]]
    
    dict_positions_oders[data.time_positions[idx1][1]], dict_positions_oders[data.time_positions[idx2][1]]=orders[idx1], orders[idx2]
    
    dict_zones[data.time_positions[idx1][0]] += data.order_sku_time[orders[idx1]] + 2 * data.s[data.time_positions[idx1]]
    dict_zones[data.time_positions[idx2][0]] += data.order_sku_time[orders[idx2]] + 2 * data.s[data.time_positions[idx2]]
    
    
    return orders, dict_zones, dict_positions_oders
def find_local_optimal_solution(data:Data, orders):
    dict_zones, dict_positions_oders=data.calculate_zones_time(orders, data.time_positions, data.order_sku_time, data.s)
    # best_max_time=abs(max(dict_zones.values())/data.max_productividad-min(dict_zones.values())/data.min_productividad)
    
    best_max_time=data.score_solution(dict_zones)
    best_positions_orders= dict_positions_oders
    best_zones= dict_zones
    
    better_max_time=best_max_time
    better_position_orders= best_positions_orders
    better_zones= best_zones
    
    T=100
    alpha=0.9
    max_iterations= 1000
    
    while T > 1 and max_iterations>0:
        # Generate a new solution by swapping two random orders
        new_orders= orders.copy()
        idx1, idx2 = random.sample(range(len(new_orders)), 2)
        new_orders, new_dict_zones, new_dict_positions_order= swap_values(data,new_orders, dict_zones, dict_positions_oders, idx1, idx2)
        # new_max_time= abs(max(new_dict_zones.values())/data.max_productividad - min(new_dict_zones.values())/data.min_productividad)
        new_max_time= data.score_solution(new_dict_zones)
        # Calculate the difference in time between the new solution and the current solution
        delta =new_max_time - better_max_time
        # If the new solution is better, accept it
        if delta <0 or random.uniform(0, 1) < math.exp(-delta / T):
            orders = new_orders.copy()
            better_max_time = new_max_time
            better_position_orders = new_dict_positions_order
            better_zones = new_dict_zones
            if better_max_time < best_max_time:
                best_max_time = better_max_time
                best_positions_orders=  better_position_orders
                best_zones = better_zones
        # Cool down the temperature
        T *= alpha
        max_iterations-=1
    
    return best_max_time, best_positions_orders, best_zones
    
    

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
        output_file=f'ils_{input_file}'
    
    archive_name=f"../data/{input_file}"
    start_time = time.time()
    data= Data(archive_name)
    print(data.max_productividad)
    print(data.min_productividad)
    max_iterations= 1000
    best_max_time= sys.maxsize

    # print(data.zones_positions)
    for i in range(max_iterations):
        orders= randomized_construction(data.orders)
        dict_zones, dict_positions_oders= data.calculate_zones_time(orders, data.time_positions, data.order_sku_time, data.s)
        lo_time, lo_positions_orders, lo_zones= find_local_optimal_solution(data, orders)
        if lo_time < best_max_time:
            best_max_time= lo_time
            best_positions_orders= lo_positions_orders
            best_zones= lo_zones
            print("Best solution found in iteration", i+1, ":", best_max_time)
    data.assign_workers(best_zones)




    data.score_solution(best_zones)
    best_max_time= data.score_solution(best_zones)
    # Write the results within an excel file
    data.write_excel(best_positions_orders, data.zones_productivity, output_file, input_file)
    # print("Best positions orders:", best_positions_orders)
    print("Best zones:", best_zones)
    print("Best zones 2:", data.zones_productivity)
    print("Productividad", data.productividad)
    print("Best solution found:", best_max_time)
    print("Workers:", data.productivity)
    print("Execution time:", time.time() - start_time)
    log_results(input_file, best_max_time, data.zones_productivity, time.time() - start_time, "ILS")