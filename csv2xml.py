# import libraries
import pandas as pd

# specify indicator, frequency, reference area, series, and reporting type
indicator_file='indicator_1-2-1.csv'
FREQ= 'A'
REF_AREA= '826'
SERIES= 'SI_POV_NAHC'
REPORTING_TYPE= 'N'

# get indicator file as dataframe and copy
original_csv=pd.read_csv(indicator_file)
indicator=pd.read_csv(indicator_file)

# when the mapping was made any spaces in column names were changed to "." so this is replicated here:
new_columns=[]
for col in indicator.columns:
    new=col.replace(" ", ".")
    indicator=indicator.rename(columns = {col:new})

# get mapping as dataframe
mapping=pd.read_csv("121_newmapping.csv")

# CREATE SOME OBJECTS
# a list of all the fields that could be present in an indicator file
fields=['FREQ', 'REPORTING_TYPE', 'SERIES', 'REF_AREA', 'SEX', 'AGE', 'URBANISATION',
                 'INCOME_WEALTH_QUANTILE', 'EDUCATION_LEV', 'OCCUPATION', 'CUST_BREAKDOWN',
                 'COMPOSITE_BREAKDOWN', 'DISABILITY_STATUS', 'TIME_PERIOD', 'OBS_VALUE',
                 'OBS_STATUS', 'UNIT_MULT', 'UNIT_MEASURE']

# a dictionary of fields created earlier
dis_values={"FREQ":FREQ, "REF_AREA":REF_AREA, "SERIES":SERIES, "REPORTING_TYPE": REPORTING_TYPE}

# empty dataframe same length as indicator data frame
df=pd.DataFrame(index=indicator.index)

# POPULATE EMPTY DATAFRAME (df)
# for each column in the indicator file create a column in df which has the
# corresponding column name from the mapping
for col in indicator.columns:
    newcol=mapping['DSD_Dim'].loc[mapping['EXT_Dim']==col].iloc[0]
    df[newcol]=indicator[col]
    indicator.rename(columns={col:newcol}, inplace=True)

# for each of the items in the fields list, check whether the field is a column
# name in the indicator file and whether it has already been specified in the
# dis_values dictionary (as it is).
# if not then add the field to the dis_values dictionary as keys, with '_T' as the values

for field in ['_REPVAR_' if x=="OBS_VALUE" else x for x in fields]:
    if field not in indicator.columns and field not in dis_values.keys():
        dis_values[field]='_T'

# for each key in the dis_values dictionary create a column in df
# and assign the corresponding value to every row in that column
for dis, value in dis_values.items():
    df[dis]=value

# fill empty cells with '_' (as that what they are in the mapping)
df=df.fillna('_')

# for each row in df, covert current value to corresponding DSD value using mapping
for i in df.index:
    for col in indicator.drop(columns=["TIME_PERIOD", "_REPVAR_"]).columns:
        df.at[i, col]=mapping['DSD_Dim_Code'].loc[mapping['EXT_Dim_Code']==df.at[i, col]].loc[mapping['DSD_Dim']==col].item()

# rename _REPVAR_ column
df.rename(columns={'_REPVAR_':'OBS_VALUE'}, inplace=True)

# sort df by disaggregation columns and reset index
df.sort_values(list(indicator.drop(columns=["TIME_PERIOD", "_REPVAR_"]).columns), inplace=True)
df=df[fields].reset_index(drop=True)
df.head()

# WRITE DATAFRAME (df) TO XML
# start by writing what is the header of the xml file created when we converted the CSV using ILOSTAT's SMART tool

# write top of xml to string called indicator_xml
indicator_xml='<?xml version="1.0" encoding="UTF-8"?>\n'
indicator_xml+='<message:StructureSpecificData xmlns:ss="http://www.sdmx.org/resources/sdmxml/schemas/v2_1/data/structurespecific" xmlns:footer="http://www.sdmx.org/resources/sdmxml/schemas/v2_1/message/footer"\n'
indicator_xml+='xmlns:ns1="urn:sdmx:org.sdmx.infomodel.datastructure.DataStructure=UNSD:SDG(0.4):ObsLevelDim:TIME_PERIOD" xmlns:message="http://www.sdmx.org/resources/sdmxml/schemas/v2_1/message"\n'
indicator_xml+='xmlns:common="http://www.sdmx.org/resources/sdmxml/schemas/v2_1/common"\n'
indicator_xml+='xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xml="http://www.w3.org/XML/1998/namespace">\n'
indicator_xml+='  <message:Header>\n'
indicator_xml+='    <message:ID>IDREF636797685310003267</message:ID>\n'
indicator_xml+='    <message:Test>false</message:Test>\n'
indicator_xml+='    <message:Prepared>2010-02-04T08:35:31</message:Prepared>\n'
indicator_xml+='    <message:Sender id="ONS"/>\n'
indicator_xml+='    <message:Structure structureID="UNSD_SDG_1_0" namespace="urn:sdmx:org.sdmx.infomodel.datastructure.DataStructure=UNSD:SDG(1.0):ObsLevelDim:TIME_PERIOD" dimensionAtObservation="TIME_PERIOD">\n'
indicator_xml+='      <common:Structure>\n'
indicator_xml+='        <Ref id="SDG" agencyID="UNSD" version="0.4"/>\n'
indicator_xml+='      </common:Structure>\n'
indicator_xml+='    </message:Structure>\n'
indicator_xml+='  </message:Header>\n'
indicator_xml+='  <message:DataSet ss:dataScope="DataStructure" xsi:type="ns1:DataSetType" ss:structureRef="UNSD_SDG_0_4">\n'


# get unique disaggregations combinations from df
unique=df.iloc[:,:13].drop_duplicates()

# create identifier column that is the same as the index column
unique["identifier"]=unique.index

# merge identifier onto full df so that we know which rows belong to a unique disaggregation column
df=df.merge(unique)

# get observation values from df
obs_values=df.iloc[:,13:]

# go through unique combos and then through each observation and write each field name and value to xml_indicator
for i in unique.index:
    xml='    <Series'
    for field in fields[:13]:
        xml +=" "+ unique[field].name +'="'+ unique[field][i]+'"'
    xml+=">\n"
    j=unique["identifier"][i]
    for k in obs_values.index:
        if j == obs_values['identifier'][k]:
            xml += "      <Obs"
            for field in fields[13:]:
                xml +=" "+ obs_values[field].name +'="'+ str(obs_values[field][k])+'"'
            xml+="/>\n"
    xml+="</Series>\n"
    indicator_xml+=xml

# end indicator_xml
indicator_xml+='  </message:DataSet>\n'
indicator_xml+='</message:StructureSpecificData>'

# write indicator_xml to indicator file with format "indicator_GOAL-TARGET-INDICATOR.xml"
with open(indicator_file.split(".")[0]+".xml", 'w') as f:
    f.write(indicator_xml)
