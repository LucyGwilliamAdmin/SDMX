def convert(indicator_code):
    import lxml.etree as ET
    import csv
    import pandas as pd
    import numpy as np


    xml_file = ET.parse(indicator_code+".xml")
    xml = xml_file.getroot()

    mapping=pd.read_csv("SDG_DSD.KG_mapping.csv") # this should be set to get a mapping that has been uploaded to the data repository
    mapping

    csv_data=pd.DataFrame()

    count=0
    for series in xml.iter('Series'):
        disaggregations=str(series.attrib).strip("{}").split(", ")
        for obs in series.findall('Obs'):
            attributes=str(obs.attrib).strip("{}").split(", ")
            for i in range(len(attributes)-1, -1, -1):
                if ":" not in attributes[i]:
                    attributes[i-1]+=", "+attributes[i]
                    del attributes[i]
            col=[]
            value=[]
            for pair1 in disaggregations:
                col.append(pair1.split(": ")[0].strip("'"))
                value.append(pair1.split(": ")[1].strip("'"))
            for pair2 in attributes:
                col.append(pair2.split(": ")[0].strip("'"))
                value.append(pair2.split(": ")[1].strip("'"))
            row=pd.DataFrame([value], columns=col)
            if count==0:
                csv_data=pd.DataFrame(columns=col)
            count+=1
            csv_data=csv_data.append(row, sort=True).reset_index(drop=True)
    csv_data.head()

    for column in csv_data:
        if len(set(list(csv_data[column])))==1 and set(list(csv_data[column]))=={"_T"}:
            csv_data.drop(columns=column, inplace=True)

    # rename OBS_VALUE column
    #csv_data.rename(columns={"OBS_VALUE":"_REPVAR_"}, inplace=True)

    csv_data.head()

    indicator=pd.DataFrame(index=csv_data.index)

    for col in csv_data:
        try:
            newcol=mapping["Codelist"].loc[mapping["Codelist"]==col].iloc[0]
            indicator[newcol]=csv_data[col]
            csv_data.rename(columns={col:newcol}, inplace=True)
        except IndexError:
            pass
    csv_data.head()

    #indicator.drop(columns=[np.nan], inplace=True)
    for i in indicator.index:
        for col in indicator.columns:
            try:
                indicator.at[i, col]=str(indicator[col].iloc[i]).replace("_T","")
                indicator.at[i, col]=mapping['Name'].loc[mapping['Code']==indicator.at[i, col]].loc[mapping['Codelist']==col].item()
            except ValueError:
                pass
    indicator.tail()

    for colname in indicator.columns:
        newcolname=colname.replace(".", " ")
        indicator.rename(columns={colname:newcolname}, inplace=True)

    indicator.replace("_", "", inplace=True)
    indicator.head()

    indicator=indicator.drop(columns=["FREQ", "REPORTING_TYPE", "SERIES", "NATURE"])
    indicator.rename(columns={"SEX":"Sex", "UNIT_MEASURE":"Unit measure", "TIME_PERIOD":"Year", "OBS_VALUE":"Value", "OBS_STATUS":"Observation status", "UNIT_MULT":"Unit multiplier", "REF_AREA":"Area"}, inplace=True)

    indicator=indicator[["Year"] +[c for c in indicator if c not in ["Year", "Value"]] + ["Value"]]

 

    for j in indicator.index:
        indicator.at[j, "Area"]=str(indicator["Area"].iloc[j]).replace("Kyrgyzstan","")
        try:
           indicator.at[j, "Value"]=float(indicator.at[j, "Value"])
        except ValueError:
           pass
        if type(indicator.at[j, "Value"])!=float:
            indicator.at[j, "Value"]=str(indicator["Value"].iloc[j]).replace(indicator.at[j, "Value"],"")
            
    
    indicator["Value"]=pd.to_numeric(indicator["Value"])

    indicator.to_csv("indicator_"+indicator_code.replace(".","-")+".csv", encoding="utf-8", index=False)