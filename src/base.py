import pandas as pd
import argparse
import random
import math
from openpyxl import Workbook
from openpyxl.styles import Border, Side, Alignment, Font


class Data:
    
    def __init__(self, excel_modelo):
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
        self.productividad = pd.read_excel(excel_modelo, 'Productividad') # Productividad de los trabajadores
        self.max_productividad = self.productividad["Productividad"].max()
        self.min_productividad = self.productividad["Productividad"].min()
        
        pedidos = list(Conjunto_pedidos.index)
        zonas = list(Conjunto_zonas.index)
        salidas = list(Conjunto_salidas.index)
        skus = list(Conjunto_skus.index)
        V = Parametros['v']
        ZN = Parametros['zn']

        self.v = float(V.iloc[0])  # Explicitly get first element
        self.zn = float(ZN.iloc[0])

        # Sort the exits by the time it takes to reach them
        s = {(j, k): Tiempo_salidas.at[j, k] for j in zonas for k in salidas if Salidas_por_zona.at[j, k] > 0}
        s = dict(sorted(s.items(), key=lambda item: item[1]))

        rp = {(i, m): Tiempo_SKU.at[i, m] for i in pedidos for m in skus if SKUS_por_pedido.at[i, m] > 0}

        # Calculate the total time an order needs to register all the SKUs
        order_sku_time = {}
        for i in pedidos:
            order_sku_time[i] = sum([rp[i, m] for m in skus if SKUS_por_pedido.at[i, m] > 0])
        self.order_sku_time = dict(sorted(order_sku_time.items(), key=lambda item: item[1], reverse=True))
        self.productividad["Productividad"]=pd.to_numeric(self.productividad["Productividad"], errors='coerce')
        self.productividad = self.productividad.sort_values("Productividad", ascending=False)["Productividad"].to_dict()
        self.orders = list(order_sku_time.keys())
        self.time_positions = list(s.keys())
        self.s=s
        self.zones_positions={k: j for j, k in s.keys()}
        self.productivity={}
    
    def print_dict(self,d, decimals=0):
        for key, value in d.items():
            if decimals > 0:
                print(key, f'{value:.{decimals}f}')
            else:
                print(key, value)

    def write_excel(self,solutions, zones, archive_name, input_filename):
        inverted_solutions = [(order, position) for position, order in solutions.items()]
        inverted_solutions_df = pd.DataFrame(inverted_solutions, columns=['Pedido', 'Salida'])
        zones_df = pd.DataFrame(list(zones.items()), columns=['Zona', 'Tiempo'])
        zones_df= zones_df.sort_values(by='Zona', ascending=True)
        max_zone = zones_df[zones_df['Tiempo'] == zones_df['Tiempo'].max()]
        data_sheet1 = {
            'Instancia': [input_filename],
            'Zona': [max_zone['Zona'].values[0]],
            'Maximo': [max(self.productivity.values())]
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

    def calculate_zones_time(self,orders, time_positions, order_sku_time, s):
        dict_zones = {}
        dict_positions_order = {}
        for i in range(len(orders)):
            dict_positions_order[time_positions[i][1]] = orders[i]
            try:
                dict_zones[time_positions[i][0]] += order_sku_time[orders[i]] + 2 * s[time_positions[i]]
            except:
                dict_zones[time_positions[i][0]] = order_sku_time[orders[i]] + 2 * s[time_positions[i]]
        return dict_zones, dict_positions_order
    def assign_workers(self, zones):
        self.zones_productivity = {}
        order_dict_zones = dict(sorted(zones.items(), key=lambda item: item[1], reverse=True))
        sorted_dict_zones = list(order_dict_zones.keys())
        for index, row in enumerate(list(self.productividad.values())):
            # self.productivity[index] = sorted_dict_zones[index]
            self.productivity[index] = zones[sorted_dict_zones[index]]/row
            self.zones_productivity[sorted_dict_zones[index]] = self.productivity[index]

    def score_solution(self, solution):
        self.assign_workers(solution)
        score = max(self.productivity.values())
        return score



# Lectura de conjuntos




def log_results(input_file, best_max_time, best_zones, execution_time, source, file_path="../output/log.txt"):
    message= (
        f"Best solution found in {input_file} using {source}: {best_max_time} within {execution_time}\n"
        f"Best zones: {best_zones}\n"
        "\n\n"
    )
    
    with open(file_path, 'a') as file:
        file.write(message)
