import pandas as pd
import argparse
import random
import math
from openpyxl import Workbook
from openpyxl.styles import Border, Side, Alignment, Font
import time
from base import log_results
from base import Data
def print_dict(d, decimals=0):
    for key, value in d.items():
        if decimals > 0:
            print(key, f'{value:.{decimals}f}')
        else:
            print(key, value)

def write_excel(solutions, zones, archive_name, input_filename):
    inverted_solutions = [(order, position) for position, order in solutions.items()]
    inverted_solutions_df = pd.DataFrame(inverted_solutions, columns=['Pedido', 'Salida'])
    zones_df = pd.DataFrame(list(zones.items()), columns=['Zona', 'Tiempo'])
    max_zone = zones_df[zones_df['Tiempo'] == zones_df['Tiempo'].max()]
    data_sheet1 = {
        'Instancia': [input_filename],
        'Zona': [max_zone['Zona'].values[0]],
        'Maximo': [round(max_zone['Tiempo'].values[0], 2)]
    }
    
    df_sheet1 = pd.DataFrame(data_sheet1)
    with pd.ExcelWriter(f'../output/{archive_name}', engine='openpyxl', mode='w') as writer:
        df_sheet1.to_excel(writer, sheet_name="Resumen", index=False)
        inverted_solutions_df.to_excel(writer, sheet_name="Soluciones", index=False)
        zones_df.to_excel(writer, sheet_name="Metricas", index=False)
        wb=writer.book
        for sheet_name in wb.sheetnames:
            ws=wb[sheet_name]
            for cell in ws[1]:  # Header is in row 1
                cell.border = Border(left=None, right=None, top=None, bottom=None)
                cell.font=Font(bold=False)
            for col in ws.columns:
                col_letter = col[0].column_letter  # Get the column letter (e.g., 'A', 'B', 'C')
                ws.column_dimensions[col_letter].bestFit = True  # Adjust the column width to fit the content
        wb.save(f'../output/{archive_name}')

def calculate_zones_time(orders, time_positions, order_sku_time, s):
    dict_zones = {}
    dict_positions_order = {}
    for i in range(len(orders)):
        dict_positions_order[time_positions[i][1]] = orders[i]
        try:
            dict_zones[time_positions[i][0]] += order_sku_time[orders[i]] + 2 * s[time_positions[i]]
        except:
            dict_zones[time_positions[i][0]] = order_sku_time[orders[i]] + 2 * s[time_positions[i]]
    return dict_zones, dict_positions_order

if __name__ == "__main__":
    start_time = time.time()
    parser = argparse.ArgumentParser(description="Orders distribution")
    parser.add_argument('input_file', type=str, help='Input file', default=None)
    parser.add_argument('output_file', type=str, help='Output file [optional]', default=None, nargs='?')
    
    args = parser.parse_args()
    if args.input_file: 
        input_file = args.input_file
    else:
        print('Please provide an input file')
        exit()
    if args.output_file:
        output_file = args.output_file
    else:
        output_file = f'simmulated_annealing_output_{input_file}'
    
    archive_name = f"../data/{input_file}"
    excel_modelo = pd.ExcelFile(archive_name)

    # Lectura de conjuntos
    Conjunto_pedidos = pd.read_excel(excel_modelo, 'Pedidos', index_col=0) # Pedidos
    Conjunto_zonas = pd.read_excel(excel_modelo, 'Zonas', index_col=0) # Zonas
    Conjunto_salidas = pd.read_excel(excel_modelo, 'Salidas', index_col=0) # Salidas
    Conjunto_skus = pd.read_excel(excel_modelo, 'SKU', index_col=0) # SKUs

    # Lectura de parametros de salidas
    N_Salidas = pd.read_excel(excel_modelo, 'Salidas_en_cada_zona', index_col=0) # Cantidad de salidas por cada zona
    Salidas_por_zona = pd.read_excel(excel_modelo, 'Salidas_pertenece_zona', index_col=0) # Parametro binario, salidas que están incluidas en cada zona
    Tiempo_salidas = pd.read_excel(excel_modelo, 'Tiempo_salida', index_col=0) # Tiempo para desplazarse desde el lector al punto medio de cada salida

    # Lectura de parametros de SKUs
    SKUS_por_pedido = pd.read_excel(excel_modelo, 'SKU_pertenece_pedido', index_col=0) # Parámetro binario, SKUS que están incluidas en un pedido
    Tiempo_SKU = pd.read_excel(excel_modelo, 'Tiempo_SKU', index_col=0) # Tiempo total de lectura, conteo, separación, depósito de cada ref por pedido

    # Lectura de parametros adicionales
    Parametros = pd.read_excel(excel_modelo, 'Parametros', index_col=0) # Parametros
    productividad = pd.read_excel(excel_modelo, 'Productividad') # Productividad de los trabajadores
    pedidos = list(Conjunto_pedidos.index)
    zonas = list(Conjunto_zonas.index)
    salidas = list(Conjunto_salidas.index)
    skus = list(Conjunto_skus.index)
    V = Parametros['v']
    ZN = Parametros['zn']

    v = float(V.iloc[0])  # Explicitly get first element
    zn = float(ZN.iloc[0])
    
    # Sort the exits by the time it takes to reach them
    s = {(j, k): Tiempo_salidas.at[j, k] for j in zonas for k in salidas if Salidas_por_zona.at[j, k] > 0}
    s = dict(sorted(s.items(), key=lambda item: item[1]))
    
    rp = {(i, m): Tiempo_SKU.at[i, m] for i in pedidos for m in skus if SKUS_por_pedido.at[i, m] > 0}
    
    # Calculate the total time an order needs to register all the SKUs
    order_sku_time = {}
    for i in pedidos:
        order_sku_time[i] = sum([rp[i, m] for m in skus if SKUS_por_pedido.at[i, m] > 0])
    order_sku_time = dict(sorted(order_sku_time.items(), key=lambda item: item[1], reverse=True))
    
    orders = list(order_sku_time.keys())
    time_positions = list(s.keys())
    
    dict_zones={}
    dict_positions_order={}

    # Setting the simulated annealing parameters
    # Initial solution

    data= Data(archive_name)
    # Randomly shuffle the orders to create an initial solution
    random.shuffle(orders)
    # Calculate the time for each zone and the order positions
    dict_zones, dict_positions_order = calculate_zones_time(orders, time_positions, order_sku_time, s)
    # Calculate the maximum time for the initial solution
    best_max_time= data.score_solution(dict_zones)
    # Initialize the best solution with the initial solution
    better_max_time=best_max_time
    better_solution = dict_positions_order
    better_zones = dict_zones

    # Initialize the best solution with the initial solution
    best_solution = dict_positions_order
    best_zones = dict_zones

    # Simulated Annealing parameters
    T=1000  # Initial temperature
    alpha=0.95  # Cooling rate
    max_iterations=1000  # Number of iterations at each temperature

    while T > 1 and max_iterations>0:
        # Generate a new solution by swapping two random orders
        new_orders= orders.copy()
        idx1, idx2 = random.sample(range(len(new_orders)), 2)
        new_orders[idx1], new_orders[idx2] = new_orders[idx2], new_orders[idx1]
        # Calculate the time for each zone and the order positions
        new_dict_zones, new_dict_positions_order = data.calculate_zones_time(new_orders, time_positions, order_sku_time, s)
        # Calculate the maximum time for the new solution
        new_max_time= data.score_solution(new_dict_zones)
        # Calculate the difference in time between the new solution and the current solution
        delta = new_max_time - better_max_time
        # If the new solution is better, accept it
        if delta <0 or random.uniform(0, 1) < math.exp(-delta / T):
            orders = new_orders.copy()
            better_max_time = new_max_time
            better_solution = new_dict_positions_order
            better_zones = new_dict_zones
            if better_max_time < best_max_time:
                best_max_time = better_max_time
                best_solution = better_solution
                best_zones = better_zones
        else:
            random.shuffle(orders)
        # Cool down the temperature
        T *= alpha
        max_iterations-=1
    
    data.assign_workers(best_zones)
    
    # Write the results within an excel file
    best_max_time=data.score_solution(best_zones)
    data.write_excel(best_solution, data.zones_productivity, output_file, input_file)
    print(f'Success Simulated Annealing, {input_file}, {best_max_time}')
    print('Best solution found:', max(data.productivity.values()))
    print("Workers assigned:", data.productivity)
    print (f'Execution time: {time.time() - start_time} seconds')
    print(len(best_solution.keys())==len(set(best_solution.keys())),len(best_solution.values())==len(set(best_solution.values())))
    log_results(input_file, best_max_time, data.zones_productivity, time.time() - start_time, 'Simulated Annealing')