import numpy as np
np.set_printoptions(suppress=True)

def bellman_algorithm(demanda,inventario, costo_pedido, costo_adquisicion, costo_almacenaje) :
    costo_minimo = float('inf')
    etapas = len(demanda)
    cantidad_adquirida = np.zeros(etapas)
    matriz1 = np.zeros((1,4))
    matriz2 = np.zeros((4,4))
    matriz3 = np.zeros((4,4))
    matriz4 = np.zeros((4,1))
    costo_min_1 = np.zeros((1,1))
    costo_min_2 = np.zeros((4,1))
    costo_min_3 = np.zeros((4,1))
    costo_min_4 = np.zeros((4,1))
    inventario_matrix_etapa_1 = np.zeros((1,1))
    inventario_matrix_etapa_1[0,0] = 0 
    contador_j = 0
    contador_i = 0
    for etapa in range(etapas-1, -1, -1):
        contador_anterior_i = 0
        contador_j = 0
        contador_i = 0
        if etapa == 3:
            for inventarios in range (0,inventario[etapa]+1):
                for adquisiciones in range (demanda[etapa]-inventario[etapa],demanda[etapa]+1):
                    if adquisiciones + inventarios == demanda [etapa]:
                        if adquisiciones > 0:
                            matriz4[contador_i][contador_j]= (adquisiciones * costo_adquisicion[etapa])
                            matriz4[contador_i][contador_j]+=costo_pedido [etapa]
                        if inventarios > 0:
                            matriz4[contador_i][contador_j]+= inventarios * costo_almacenaje[etapa]
                        contador_i = contador_i + 1
        elif etapa ==2:
            for inventarios in range (0, inventario[etapa]+1):
                contador_anterior_i = 0
                contador_j = 0
                for adquisiciones in range(demanda[etapa]-inventario[etapa], demanda[etapa]+4):
                    if demanda[etapa]<=adquisiciones + inventarios <= demanda[etapa]+3:
                        if adquisiciones > 0:
                                
                            costo_min_4[contador_anterior_i][0]= np.min(matriz4[contador_anterior_i,:])
                            matriz3[contador_i][contador_j]= (adquisiciones * costo_adquisicion[etapa]) + np.min(matriz4[contador_anterior_i, :])
                            matriz3[contador_i][contador_j]+=costo_pedido [etapa]
                        if inventarios > 0:
                            matriz3[contador_i][contador_j]+= inventarios * costo_almacenaje[etapa]
                        contador_anterior_i = contador_anterior_i + 1
                        contador_j = contador_j + 1

                contador_i = contador_i + 1
        elif etapa ==1:
            for inventarios in range (0, inventario[etapa]+1):
                contador_anterior_i = 0
                contador_j = 0
                for adquisiciones in range(demanda[etapa]-inventario[etapa], demanda[etapa]+4):
                    if demanda[etapa]<=adquisiciones + inventarios <= demanda[etapa]+3:
                        if adquisiciones > 0:
                                
                            costo_min_3[contador_anterior_i][0]= np.min(matriz3[contador_anterior_i,:])
                            matriz2[contador_i][contador_j]= (adquisiciones * costo_adquisicion[etapa]) + np.min(matriz3[contador_anterior_i, :])
                            matriz2[contador_i][contador_j]+=costo_pedido [etapa]
                        if inventarios > 0:
                            matriz2[contador_i][contador_j]+= inventarios * costo_almacenaje[etapa]
                        contador_anterior_i = contador_anterior_i + 1
                        contador_j = contador_j + 1

                contador_i = contador_i + 1
        elif etapa == 0:
            inventarios = 0
            contador_anterior_i = 0
            contador_j = 0
            for adquisiciones in range(demanda[etapa], demanda[etapa]+4):
                if adquisiciones + inventarios >= demanda[etapa]:
                    if adquisiciones > 0:
                        
                        costo_min_2[contador_anterior_i][0]= np.min(matriz2[contador_anterior_i,:])
                        matriz1[contador_i][contador_j]= (adquisiciones * costo_adquisicion[etapa]) + np.min(matriz2[contador_anterior_i, :])
                        matriz1[contador_i][contador_j]+=costo_pedido [etapa]
                    if inventarios > 0:
                        matriz1[contador_i][contador_j]+= inventarios * costo_almacenaje[etapa]
                    if matriz1[contador_i][contador_j]<costo_minimo:
                        costo_minimo = matriz1[contador_i][contador_j]
                        cantidad_optima = adquisiciones 
                    contador_anterior_i = contador_anterior_i + 1
                    contador_j = contador_j + 1
            costo_min_1[0,0]= np.min(matriz1[0,:])
    
    for etapa in range(0, etapas):
        
        if etapa == 0:
            i = 0
            for adquisiciones in range (demanda[etapa], demanda[etapa]+4):
                if matriz1[0,i] == costo_min_1[0,0]:
                    cantidad_adquirida[etapa]= adquisiciones
                i =i +1

        elif etapa == 1:
            cantidad_sobrante= np.zeros(4)
            cantidad_sobrante[etapa-1] = demanda[etapa-1] - cantidad_adquirida[etapa-1]
            j = 0
            inventarios = int(cantidad_sobrante[etapa-1])
            for adquisiciones in range (demanda[etapa]-inventario[etapa],demanda[etapa]+4):
                if demanda[etapa]<=adquisiciones + inventarios <= demanda[etapa]+3:
                    if matriz2[inventarios,j] == costo_min_2[inventarios,0]:
                        cantidad_adquirida[etapa] = adquisiciones
                    j = j + 1
        elif etapa == 2:
            cantidad_sobrante= np.zeros(4)
            cantidad_sobrante[etapa-1] = demanda[etapa-1] - cantidad_adquirida[etapa-1]
            j = 0
            inventarios = int(cantidad_sobrante[etapa-1])
            for adquisiciones in range (demanda[etapa]-inventario[etapa],demanda[etapa]+4):
                if demanda[etapa]<=adquisiciones + inventarios <= demanda[etapa]+3:
                    if matriz3[inventarios,j] == costo_min_3[inventarios,0]:
                        cantidad_adquirida[etapa] = adquisiciones
                    j = j + 1
        elif etapa == 3:
            cantidad_sobrante= np.zeros(4)
            cantidad_sobrante[etapa-1] = demanda[etapa-1] - cantidad_adquirida[etapa-1]
            j = 0
            inventarios = int(cantidad_sobrante[etapa-1])
            for adquisiciones in range (demanda[etapa]-inventario[etapa],demanda[etapa]+1):
                    if matriz4[inventarios,0] == costo_min_4[inventarios,0]:
                        cantidad_adquirida[etapa] = adquisiciones
                    j = j + 1

       




    # print ("Etapa 4:")
    # matriz_resultante4 = np.hstack((matriz4, costo_min_4))
    # matriz_resultante4 = np.hstack((inventario_matrix,matriz_resultante4))
    # print(matriz_resultante4)
    # print ("Etapa 3:")
    # matriz_resultante3 = np.hstack((matriz3, costo_min_3))
    # matriz_resultante3 = np.hstack((inventario_matrix,matriz_resultante3))
    # print(matriz_resultante3)
    # print ("Etapa 2:")
    # matriz_resultante2 = np.hstack((matriz2, costo_min_2))
    # matriz_resultante2 = np.hstack((inventario_matrix,matriz_resultante2))
    # print(matriz_resultante2)
    # print ("Etapa 1:")
    # matriz_resultante1 = np.hstack((matriz1, costo_min_1))
    # matriz_resultante1 = np.hstack((inventario_matrix_etapa_1,matriz_resultante1))
    # print(matriz_resultante1)
    return cantidad_adquirida
