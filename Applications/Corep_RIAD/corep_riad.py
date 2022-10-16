# File: matching_tool.py
# Last saved: 26 November 2021
# Version: 2.0

#---------------------------------------
#    Launching the PySpark session                     
#---------------------------------------

from pyspark.sql import SparkSession, SQLContext
from pyspark import SparkConf, SparkContext
from pyspark_matching import *

configuration_cluster = (
    SparkConf()
    .set("spark.executor.cores", "4")
    .set("spark.dynamicAllocation.maxExecutors", "20")
    .set("spark.executor.memory", "20g")
    .set("spark.driver.memory", "16g")
    .set("spark.driver.maxResultSize", "8g")
    .set("spark.sql.shuffle.partitions", "200")
    .set("spark.kryoserializer.buffer.max", "1g")
    .set("spark.dynamicAllocation.enabled", "true")
    .set("spark.network.timeout", "180000")
    .set("spark.sql.execution.arrow.pyspark.enabled", "true")
)

spark = (
    SparkSession.builder.appName("corep_riad")
    .config(conf=configuration_cluster)
    .master("yarn")
    .enableHiveSupport()
    .getOrCreate()
)

  #-------------------------
  # Loading the two datasets
  #-------------------------
  
 #------------
 # RIAD 
 #------------

# Load data and select all the relevant attributes
dataset1_original = spark.read.parquet("/data/corporate/riad_n_essential/riad_entty_flttnd_essntl_d_1/")\
                         .select('entty_riad_cd', 'nm_entty', 'cntry').dropDuplicates()
  
 # RIAD attribute names
 # - address, city and postal code are optional attributes
 # - if an optional attribute is not available, write NA in both datasets

id_data1 = 'entty_riad_cd' 
name_data1 = 'nm_entty'
country_1 = 'cntry'
street_data1 = 'NA'
city_data1 = 'NA'
pstl_data1 = 'NA'


 # Specify which type of country attribute you have. It can differ between the 2 datasets 
 # Possible values: 
 # - 'country_name': if you have the extended name of the country 
 # - 'isocode2': if you have the isocode with 2 digits
 # - 'isocode3': if you have the iscode with 3 digits

country_attribute = 'isocode2'

 #-------------
 # Corep
 #-------------
# Load data and select all the relevant attributes
from connectors import disc 

query ='''SELECT DISTINCT c_0602_c0010 as sub_name, c_0602_c0050 as sub_cntry
          FROM crp_suba.suba_c_0602
          WHERE reported_period < '2021-06%'

          UNION

          SELECT DISTINCT coalesce(c_0602_rx15_c0011, c_0602_rx16_c0011) as sub_name, 
                       coalesce(c_0602_rx15_c0050, c_0602_rx16_c0050) as sub_cntry
          FROM crp_suba.suba_c_0602 
          WHERE reported_period >= '2021-06%'
          '''

corep = disc.read_sql(query)

dataset2_original = spark.createDataFrame(corep)\
                         .withColumn('id_name', col('sub_name'))


 # Corep attribute names

id_data2 = 'id_name'
name_data2 = 'sub_name'
country_2 = 'sub_cntry'
street_data2 = 'NA'
city_data2 = 'NA'
pstl_data2 = 'NA'


 # Specify which type of country attribute you have. 
country_attribute2 = 'country_name'

#----------------------------
# Use of Fuzzy-name dictionary
#----------------------------

fuzzy_wuzzy = True 
fuzzy_levels = 1 #possible values = 1,2,3
  
  #If true the fuzzywuzzy dictionary will be applied to the names of the entities
  #Rules of thumb:
  # - use it when the tool is used in its complete version (all attributes)
  # - the higher the level, the less precise and computationally more inefficient the tool will be 
  #   but you may get more matchings (suggested value = 1)
  
#----------------------------
# Hyperparameters of address similarity
#----------------------------
  
  # Use similarity on address
address_similarity = True

  # If you accept differences on the address you can modifiy the following:
  
first_split = 10   # Length of the address to create the first group
diff_group1 = 4    # Dissimilarities accepted for the first group

second_split = 20  # Length of the address to create the second and third groups
diff_group2 = 7    # Dissimilarities accepted for the second group 
diff_group3 = 9    # Dissimilarities accepted for the third group, with length(address) > second split


#-------------------------------------
# Add a column with a similarity score
#-------------------------------------

add_column_score = False

#--------------------------------------
# Define path to save the mapping table
#--------------------------------------

save_table = True # if you don't want to save the table modify with False
disc_lab = 'lab_prj_dcaap_open' # only data lab allowed, no corporate store
table_name = 'riad_corep_mapping' # name of the table
  
  
#------------------------
# --> Run the tool
#------------------------

name_matches = fuzzyNameMatching(spark,
                                 dataset1_original, id_data1, name_data1, country_1, street_data1, city_data1, pstl_data1,country_attribute,
                                 dataset2_original, id_data2, name_data2, country_2, street_data2, city_data2, pstl_data2,country_attribute2,
                                 fuzzy_wuzzy, fuzzy_levels,
                                 address_similarity, first_split, diff_group1, second_split, diff_group2, diff_group3,
                                 add_column_score,
                                 save_table, disc_lab, table_name)




spark.stop()
