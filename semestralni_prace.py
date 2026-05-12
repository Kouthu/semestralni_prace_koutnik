import arcpy
import os
import sys

def nacti_vstupy_uzivatele():
    """
    Pomocná funkce pro interaktivní načtení parametrů od uživatele.
    """
    print("--- NASTAVENÍ PARAMETRŮ ANALÝZY ---")
    workspace = input("Zadejte cestu ke své Geodatabázi (GDB): ")
    zajmove_uzemi = input("Zadejte cestu k vrstvě zájmového území (hranice): ")
    
    print("\nZadejte seznam vstupních bodových vrstev (oddělené čárkou).")
    print("Příklad: body_vychod, body_stred, body_sever")
    vstupy_raw = input("Vstupy: ")
    seznam_bodu = [v.strip() for v in vstupy_raw.split(",")]
    
    velikost = input("\nZadejte velikost čtverce s jednotkou (např. '1 SquareKilometers'): ")
    
    return workspace, zajmove_uzemi, seznam_bodu, velikost

def spust_opakovatelnou_analyzu(workspace, hranice, seznam_bodu, velikost_site):
    """
    Hlavní procesní funkce, která je nyní plně parametrizovaná.
    """
    try:
        arcpy.env.workspace = workspace
        arcpy.env.overwriteOutput = True
        
        # Ověření existence workspace
        if not arcpy.Exists(workspace):
            raise ValueError(f"Chyba: Workspace {workspace} neexistuje!")

        # 1. Generování sítě (Tessellation)
        print(f"\n[1/4] Generuji čtvercovou síť o velikosti {velikost_site}...")
        grid = os.path.join(workspace, "generovana_sit_tess")
        arcpy.management.GenerateTessellation(grid, hranice, "SQUARE", velikost_site)

        do_mergu = []

        # 2. Agregace dat (Summarize Within) v cyklu
        print(f"[2/4] Začínám agregaci pro {len(seznam_bodu)} vrstev...")
        for i, vrstva in enumerate(seznam_bodu):
            if not arcpy.Exists(vrstva):
                print(f" ! Varování: Vrstva {vrstva} nebyla nalezena, přeskakuji.")
                continue
                
            vystup_agregace = os.path.join(workspace, f"tmp_agregace_{i}")
            print(f" -> Zpracovávám: {vrstva}")
            
            arcpy.analysis.SummarizeWithin(
                in_polygons=grid,
                in_sum_features=vrstva,
                out_feature_class=vystup_agregace,
                sum_fields=[["BOBYOSL21", "SUM"]]
            )
            do_mergu.append(vystup_agregace)

        # 3. Merge a 4. Clip
        if do_mergu:
            print("[3/4] Spojuji výsledky do jednoho celku...")
            tmp_merge = os.path.join(workspace, "tmp_merged_layer")
            arcpy.management.Merge(do_mergu, tmp_merge)
            
            print("[4/4] Ořezávám výslednou vrstvu podle zájmového území...")
            finalni_vystup = os.path.join(workspace, "VYSLEDEK_AGREGACE_KOUTNIK")
            arcpy.analysis.Clip(tmp_merge, hranice, finalni_vystup)
            
            print(f"\nHOTOVO! Výsledek najdete zde: {finalni_vystup}")
        else:
            print("Chyba: Nebyla vytvořena žádná data k sjednocení.")

    except arcpy.ExecuteError:
        print(arcpy.GetMessages(2))
    except Exception as e:
        print(f"Neočekávaná chyba: {e}")

if __name__ == "__main__":
    # 1. Načtení dat od uživatele
    ws, hranice, body, rozmer = nacti_vstupy_uzivatele()
    
    # 2. Spuštění samotného výpočtu
    spust_opakovatelnou_analyzu(ws, hranice, body, rozmer)