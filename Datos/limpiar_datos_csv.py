import pandas as pd
import copy

df = pd.read_csv("Datos/Crudo/metro_stations.csv")

mas_de_uno = df["Name"].value_counts()
mas_de_uno = mas_de_uno[mas_de_uno >1]

new_df = copy.copy(df)#Copia del df
nuevas_lineas = ""
#For que recorre los nombre de las estaciones de más de una línea
for index in mas_de_uno.index:
    lineas = df[df["Name"] == index].LineID #Saca las lineas
    nuevas_lineas = ""
    for e in lineas:
        nuevas_lineas += e + ", "
    nuevas_lineas = nuevas_lineas[:len(nuevas_lineas)-2]#variable que guarda el nuevo valor de las lineas

    filas = df[df["Name"] == index].copy()#Saco un df con todos los elementos de la estación con varias estaciones
    new_df.loc[filas.index[0], "LineID"] = nuevas_lineas.strip('"')#Cambia la primera ocurrencia con varias lineas por todas las líneas
    
    filas.drop(filas.index[0], inplace=True)#Quito la primera fila, ya que sobre esa fila solo voy a cambiar el valor LineID por el nuevo
    
    #Borra todas las otras filas que no queremos
    for inx in filas.index:
        new_df.drop(inx, inplace=True)


nuevos_ids = list(range(1,len(new_df)+1))#Lista de 1 hasta la longitud del dataframe para los nuevos IDs
new_df["ID"] = nuevos_ids
new_df = new_df.reset_index(drop=True)#Reiniciar los index de las filas

print(type(new_df.loc[0, "LineID"]))

new_df.to_csv("Datos/Limpio/metro_stations_clean.csv", index=False)#Guardar el nuevo csv 

