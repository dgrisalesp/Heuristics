import pandas as pd
import argparse
import random
import math
from openpyxl import Workbook
from openpyxl.styles import Border, Side, Alignment, Font
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
    import time
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
        output_file = f'randomized_output_{input_file}'
    
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
    
    data= Data(archive_name)
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
    
    print(time.time() - start_time)
    
    best_solution = None
    best_zones = None
    best_max_time = float('inf')
    
    # Randomize 10 times and select the best solution
    for _ in range(1000):
        random.shuffle(orders)
        dict_zones, dict_positions_order = data.calculate_zones_time(orders, time_positions, order_sku_time, s)
        max_time = data.score_solution(dict_zones)
        
        if max_time < best_max_time:
            best_max_time = max_time
            best_solution = dict_positions_order
            best_zones = dict_zones
    
    # Assign the best solution to workers
    
    # Write the results within an excel file
    write_excel(best_solution, best_zones, output_file, input_file)
    print(f'Success Randomized, {input_file}, {max(data.productivity.values())}')
    
