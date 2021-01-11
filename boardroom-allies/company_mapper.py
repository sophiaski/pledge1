#!/usr/bin/env python
"""
This script reads inp from STDIN and returns a Pandas DataFrame of
 of customized strings of affiliated individuals and companies.
INPUT:
    * .txt file of company names
    * Boolean string
OUTPUT FORMAT:
    Pandas DataFrame
USAGE:
    python company_mapper.py < 'companyA,companyB,...'

Overview:

    1. Use autocompletes function to find the input company's uuid.
    2. Use makequery_board_affiliations and go_past_1000
    functions to pull all current and former board affiliations
     of the input company.
    3. Use primary_info function to obtain primary job title, primary
    organization, and LinkedIn of each individual.
    4. Transform affiliations into dictionaries of concatenated
    strings. Save to CSV file.
    5. Use makequery_investors and go_past_1000 functions to pull
    all investors of the input company.
    6. Transform investment information into dictionaries of
    concatenated strings. Update CSV file & print out results.

"""
# Import relevant libraries
import sys
import requests
import json
from json import JSONDecodeError
import pandas as pd
from pandas import json_normalize

# P1s Crunchbase API user key
from user_key import userkey
# API POST methods
from p1_crunchbase import url_count, url_extraction, go_past_1000
# API GET methods
from p1_crunchbase import autocompletes, primary_info, primary_info_of_people
# Strings
from p1_crunchbase import create_board_strings, create_investor_strings
# Column formatter
from p1_crunchbase import column_mapper
# Finance round formatters
from p1_crunchbase import order_mapper, abbrev_mapper
# Query methods
from p1_queries import makequery_investors, makequery_board_affiliations

# Functions for this script
def get_uuid(x):
    try:
        return x[0]['uuid']
    except:
        return x

def get_value(x):
    try:
        return x[0]['value']
    except:
        return x

def str_to_bool(s):
    if s == 'True':
         return True
    elif s == 'False':
         return False
    else:
         raise ValueError # evil ValueError that doesn't tell you what the wrong value was


    # this accepts the user's input
    # and stores in inp
    #input("Type anything")

    # prints inp
    #print(inp)

def main():
    """main
    """
    if len(sys.argv)<=1:
        print('Missing input!')
        pass
    elif len(sys.argv)==2:
        print("Missing an argument. The script takes a company string and 'True/False'")
        pass
    else:
        print_outputs = str_to_bool(sys.argv[2])
        search_input = open("input.txt", "r").read().split('\n')
        print(search_input)

    ################
    # SEARCH INPUT #
    ################

    # Set global variable
    global raw

    # Save output uuid and value from search results
    uuid = []
    found_item = []
    print('Count to {}:'.upper().format(len(search_input)), end=' ')
    for idx,item in enumerate(search_input):
        print(str(idx+1), end=' ')
        uuid_found,value_found = autocompletes(item, 'organizations', limit=1, verbose=print_outputs)
        uuid.append(uuid_found)
        found_item.append(value_found)
    add_uuid_to_df = dict(zip(found_item,uuid))

    ######################
    # BOARD AFFILIATIONS #
    ######################

    # Reset global variable
    raw = pd.DataFrame()
    # Make query of current/former board affiliations of companies
    query = makequery_board_affiliations(uuid)
    # Run query w/ API call, which populates dataframe with query results
    comp_count = url_count(query, 'jobs')
    raw = go_past_1000(query, 'jobs', comp_count, raw)

    # Filter down the query dataframe to usable fields
    aff = raw[['properties.organization_identifier.value',  # Company name
               'properties.person_identifier.uuid', # Person UUID
               'properties.person_identifier.value',  # Person name
               'properties.title',  # Job title of board affiliation
               'properties.job_type',  # Crunchbase job_type
               'properties.is_current'] # Boolean of whether job is current or not
             ].sort_values(['properties.organization_identifier.value']).reset_index(drop=True) # Sory by company name
    aff.rename(column_mapper, axis=1, inplace=True)

    # Get uuids of people
    board_uuids = list(set(aff['person_uuid'].to_list()))
    # Pull unique list of company names from series
    company_names = sorted(list(set(aff['company'].to_list())))

    # Display
    print('\n\nAFFILIATIONS')
    print('Number of companies: {}'.format(len(company_names)))
    print('Total affiliations found: {}'.format(aff.shape[0]))
    print('Total unique affiliations found: {}\n'.format(len(board_uuids)))

    # Add primary title, primary organization, and LinkedIn to aff dataframe
    _,titles,orgs,_,linkedin = primary_info_of_people(board_uuids)
    aff['person_title'] = aff['person_uuid'].map(titles)
    aff['primary_org'] = aff['person_uuid'].map(orgs)
    aff['person_linkedin'] = aff['person_uuid'].map(linkedin)

    # Current board members
    current_board_members = aff[((aff['is_current'])|(pd.isnull(aff['is_current'])))&(aff['job_type']=='board_member')].sort_values(['person'])
    # Former board members
    former_board_members = aff[(aff['is_current']==False)&(aff['job_type']=='board_member')].sort_values(['person'])
    # Current board advisors/observers
    current_board_other = aff[((aff['is_current'])|(pd.isnull(aff['is_current'])))& (aff['job_type']!='board_member')].sort_values(['person'])
    # Former board advisors/observers
    former_board_other = aff[(aff['is_current']==False)&(aff['job_type']!='board_member')].sort_values(['person'])

    # To iterate through
    frames = [current_board_members, former_board_members, current_board_other, former_board_other]

    #############
    # INVESTORS #
    #############

    # Reset global variable
    raw = pd.DataFrame()

    # Make query of investments in company
    query = makequery_investors(uuid)

    # Run query w/ API call, which populates dataframe with query results
    comp_count = url_count(query, 'investments')
    raw = go_past_1000(query, 'investments', comp_count, raw)

    # Create dataframe that contains the investor name, org name, and type of investment (for grouping)
    investors = raw[['properties.investor_identifier.uuid',
                     'properties.investor_identifier.value',
                     'properties.identifier.value',
                     'properties.organization_identifier.value',
                     'properties.partner_identifiers']
                   ].sort_values('properties.organization_identifier.value').reset_index(drop=True)
    investors['properties.investor_identifier.value'] = investors['properties.investor_identifier.value'].str.strip('-')

    # Extract financing type from title string
    investors['type'] = investors['properties.identifier.value'].str.partition(' - ')[0].str.partition(' in ')[2]

    # Map uuids w/ custom dictionnaries to add new dataframe columns
    investors['partner_uuid'] = investors['properties.partner_identifiers'].apply(get_uuid)
    investors['partner_name'] = investors['properties.partner_identifiers'].apply(get_value)
    investors = investors.drop(['properties.identifier.value','properties.partner_identifiers'], axis=1)
    investors = investors.fillna('Not Listed')

    # Send through column_mapper
    investors.rename(column_mapper, axis=1, inplace=True)

    # Remove duplicates
    investors = pd.DataFrame(investors.groupby(['investor_uuid','investor_name','company','type','partner_uuid','partner_name']).count().reset_index())

    print('INVESTMENTS')
    print('Number of companies: {}'.format(len(company_names)))
    print('Total investments found: {}'.format(investors.shape[0]))
    print('Total unique investors found: {}\n'.format(len(investors.investor_name.unique())))

    ####################
    # CREATE DATAFRAME #
    ####################

    map_dict = create_board_strings(frames, company_names)
    investors_all, investors_w_info = create_investor_strings(investors)
    map_dict.append(investors_all)
    map_dict.append(investors_w_info)

    # Start mapping dataframe
    aff_mapper = {}
    columns = ['Current Board Members','Former Board Members',
               'Current Board Advisors/Observers','Former Board Advisors/Observers',
               'Investors (All)','Investors (w/ Info)']
    for key in company_names:
        aff_mapper[key] = [map_dict[0][key],map_dict[1][key],map_dict[2][key],map_dict[3][key],map_dict[4][key],map_dict[5][key]]
    mapping = pd.DataFrame.from_dict(aff_mapper, orient='index', columns=columns).reset_index().rename({'index':'Company'},axis=1)
    mapping['uuid'] = mapping['Company'].map(add_uuid_to_df)
    mapping = mapping[['uuid','Company','Current Board Members','Former Board Members','Current Board Advisors/Observers',
     'Former Board Advisors/Observers','Investors (All)','Investors (w/ Info)']]

    ##################
    # PRINT & OUTPUT #
    ##################

    # Output
    if mapping.shape[0]==1:
        print('*'*50)
        print('Results for {}'.format(value_found.upper()))
        print('*'*50)
        for idx,col in enumerate(mapping.columns):
            print('{}:\n{}\n\n'.format(col.upper(), mapping.loc[0,col]))

    mapping.to_csv('output.csv', index=False)

if __name__ == "__main__":
    main()
