import pandas as pd

def trova_record_comuni(file_a, file_b, file_c, output_file='output.csv'):
    """
    Trova i record con 'name' presente in tutti e tre i file e combina
    le colonne PixelX e PixelY di ciascun file in un'unica riga.
    
    Args:
        file_a (str): Path del primo file CSV
        file_b (str): Path del secondo file CSV
        file_c (str): Path del terzo file CSV
        output_file (str): Path del file di output (default: 'output.csv')
    
    Returns:
        DataFrame: DataFrame con i risultati
    """
    
    # Leggi i tre file CSV
    df_a = pd.read_csv(file_a)
    df_b = pd.read_csv(file_b)
    df_c = pd.read_csv(file_c)
    
    # Verifica che le colonne necessarie esistano
    colonne_richieste = ['name', 'PixelX', 'PixelY']
    for nome_file, df in [('A', df_a), ('B', df_b), ('C', df_c)]:
        if not all(col in df.columns for col in colonne_richieste):
            raise ValueError(f"Il file {nome_file} deve contenere le colonne: {colonne_richieste}")
    
    # Trova i nomi presenti in tutti e tre i file
    nomi_a = set(df_a['name'])
    nomi_b = set(df_b['name'])
    nomi_c = set(df_c['name'])
    
    nomi_comuni = nomi_a & nomi_b & nomi_c
    
    print(f"Trovati {len(nomi_comuni)} nomi comuni in tutti e tre i file")
    
    # Filtra i dataframe per i nomi comuni
    df_a_filtrato = df_a[df_a['name'].isin(nomi_comuni)][['name', 'PixelX', 'PixelY']]
    df_b_filtrato = df_b[df_b['name'].isin(nomi_comuni)][['name', 'PixelX', 'PixelY']]
    df_c_filtrato = df_c[df_c['name'].isin(nomi_comuni)][['name', 'PixelX', 'PixelY']]
    
    # Rinomina le colonne per distinguere i file
    df_a_filtrato = df_a_filtrato.rename(columns={
        'PixelX': 'PixelX_A',
        'PixelY': 'PixelY_A'
    })
    df_b_filtrato = df_b_filtrato.rename(columns={
        'PixelX': 'PixelX_B',
        'PixelY': 'PixelY_B'
    })
    df_c_filtrato = df_c_filtrato.rename(columns={
        'PixelX': 'PixelX_C',
        'PixelY': 'PixelY_C'
    })
    
    # Unisci i dataframe basandosi sul nome
    risultato = df_a_filtrato.merge(df_b_filtrato, on='name')
    risultato = risultato.merge(df_c_filtrato, on='name')
    
    # Ordina per nome
    risultato = risultato.sort_values('name').reset_index(drop=True)
    
    # Salva il risultato
    risultato.to_csv(output_file, index=False)
    print(f"Risultati salvati in '{output_file}'")
    
    return risultato


# Esempio di utilizzo
if __name__ == "__main__":
    # I file devono chiamarsi A.csv, B.csv, C.csv
    file_a = 'A.csv'
    file_b = 'B.csv'
    file_c = 'C.csv'
    
    try:
        risultato = trova_record_comuni(file_a, file_b, file_c)
        
        print("\nPrime 5 righe del risultato:")
        print(risultato.head())
        
        print("\nColonne del risultato:")
        print(risultato.columns.tolist())
        
    except FileNotFoundError as e:
        print(f"Errore: File non trovato - {e}")
    except ValueError as e:
        print(f"Errore: {e}")
    except Exception as e:
        print(f"Errore imprevisto: {e}")