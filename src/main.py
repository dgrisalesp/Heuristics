import pandas as pd, time
import argparse
# import numpy as np
import openpyxl
from openpyxl.styles import Border, Font
from base import log_results
def print_dict(d, decimals=0):
    for key,value in d.items():
        if decimals>0:
            print(key,f'{value:.{decimals}f}')
        else:
            print(key,value)
            

def write_excel(solutions, zones, archive_name, input_filename):
    inverted_solutions = [(order, position) for position, order in solutions.items()]
    solutions_df = pd.DataFrame(inverted_solutions, columns=['Pedido', 'Salida'])
    zones_df=pd.DataFrame(list(zones.items()),columns=['Zona','Tiempo'])
    max_zone=zones_df[zones_df['Tiempo']==zones_df['Tiempo'].max()]
    data_sheet1={
    'Instancia': [input_filename],
     'Zona': [max_zone['Zona'].values[0]],
     'Maximo':[round(max_zone['Tiempo'].values[0],2)]}
    
    df_sheet1=pd.DataFrame(data_sheet1)
    with pd.ExcelWriter(f'../output/{archive_name}', engine='openpyxl', mode='w') as writer:
            df_sheet1.to_excel(writer, sheet_name="Resumen", index=False)
            solutions_df.to_excel(writer, sheet_name="Soluciones", index=False)
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
if __name__ == "__main__":
    start_time = time.time()
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
        output_file=f'output_{input_file}'
    
    archive_name=f"../data/{input_file}"
    excel_modelo = pd.ExcelFile(archive_name)

    #Lectura de conjuntos
    Conjunto_pedidos = pd.read_excel(excel_modelo, 'Pedidos', index_col=0) #Pedidos
    Conjunto_zonas = pd.read_excel(excel_modelo, 'Zonas', index_col=0) #Zonas
    Conjunto_salidas = pd.read_excel(excel_modelo, 'Salidas', index_col=0) #Salidas
    Conjunto_skus = pd.read_excel(excel_modelo, 'SKU', index_col=0) #SKUs
    #Conjunto_trabajadores = pd.read_excel(excel_modelo, 'Trabajadores', index_col=0) #Trabajadores

    #Lectura de parametros de salidas
    N_Salidas = pd.read_excel(excel_modelo, 'Salidas_en_cada_zona', index_col=0) #Cantidad de salidas por cada zona
    Salidas_por_zona = pd.read_excel(excel_modelo, 'Salidas_pertenece_zona', index_col=0) #Parametro binario, salidas que están incluidas en cada zona
    Tiempo_salidas = pd.read_excel(excel_modelo, 'Tiempo_salida', index_col=0) #Tiempo para desplazarse desde el lector al punto medio de cada salida

    #Lectura de parametros de SKUs
    SKUS_por_pedido = pd.read_excel(excel_modelo, 'SKU_pertenece_pedido', index_col=0) #Parámetro binario, SKUS que están incluidas en un pedido
    Tiempo_SKU = pd.read_excel(excel_modelo, 'Tiempo_SKU', index_col=0) #Tiempo total de lectura, conteo, separación, depósito de cada ref por pedidotr

    #Lectura de parametros adicionales
    Parametros = pd.read_excel(excel_modelo, 'Parametros', index_col=0) #Parametros
    productividad=pd.read_excel(excel_modelo, 'Productividad') #Productividad de los trabajadores
    pedidos = list(Conjunto_pedidos.index)
    zonas = list(Conjunto_zonas.index)
    salidas = list(Conjunto_salidas.index)
    skus = list(Conjunto_skus.index)
    V = Parametros['v']
    ZN = Parametros ['zn']


    v = float(V.iloc[0])  # Explicitly get first element
    zn = float(ZN.iloc[0])
    
    
    #Sort the exits by the time it takes to reach them
    s = {(j, k): Tiempo_salidas.at[j,k] for j in zonas for k in salidas if Salidas_por_zona.at[j, k] > 0}
    s = dict(sorted(s.items(), key=lambda item: item[1]))
    
    
    rp={(i,m):Tiempo_SKU.at[i,m] for i in pedidos for m in skus if SKUS_por_pedido.at[i,m]>0}
    
    
    #Calculate the total time an order needs to register all the SKUs
    order_sku_time={}
    for i in pedidos:
        order_sku_time[i]=sum([rp[i,m] for m in skus if SKUS_por_pedido.at[i,m]>0])
    order_sku_time=dict(sorted(order_sku_time.items(), key=lambda item: item[1], reverse=True))
    
    orders=list(order_sku_time.keys())
    time_positions=list(s.keys())
    dict_zones={}
    dict_positions_order={}
    i=0
    #Assign the orders to the positions, the most time consuming orders are assigned to the positions that take the least time to reach the exits
    
    while i<len(orders):
        dict_positions_order[time_positions[i][1]]=orders[i]
        try:
            dict_zones[time_positions[i][0]]+=order_sku_time[orders[i]]+2*s[time_positions[i]]
            
        except:
            dict_zones[time_positions[i][0]]=order_sku_time[orders[i]]+2*s[time_positions[i]]
        i+=1
    
    #Order the zones by the time it takes to process the orders
    #Assign the most productive worker to the zone that takes the most time to process the orders
    
    order_dict_zones=dict(sorted(dict_zones.items(), key=lambda item: item[1], reverse=True))
    sorted_dict_zones=list(order_dict_zones.keys())
    for index, row in productividad.iterrows():
        productividad.at[index,'Worker']=sorted_dict_zones[index]
        productividad.at[index,'Time']=dict_zones[sorted_dict_zones[index]]/row['Productividad']
        dict_zones[sorted_dict_zones[index]]=dict_zones[sorted_dict_zones[index]]/row['Productividad']  
    # print_dict(dict_zones,2)
    # print('\n\n')
    print(productividad)        
    # print(dict_positions_order)
    
    #Write the results within an excel file
    write_excel(dict_positions_order, dict_zones, output_file, input_file)
    # print(dict_zones)
    print(f'Success Constructive, {input_file}, {max(dict_zones.values())}')
    log_results(input_file, max(dict_zones.values()), productividad, time.time() - start_time, 'Constructive')
