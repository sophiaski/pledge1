import requests
import json
from json import JSONDecodeError
import pandas as pd
from pandas import json_normalize
from user_key import userkey

# Column/field mapper dictionnairies
column_mapper = {'properties.organization_identifier.value':'company',
                 'properties.person_identifier.value':'person',
                 'properties.person_identifier.uuid':'person_uuid',
                 'properties.title':'title',
                 'properties.job_type':'job_type',
                 'properties.started_on.value':'started_on',
                 'properties.ended_on.value':'ended_on',
                 'properties.is_current':'is_current',
                 'properties.updated_at':'record_last_updated',
                 'properties.investor_identifier.uuid':'investor_uuid',
                 'properties.investor_identifier.value':'investor_name',
                 'identifier.uuid':'uuid',
                 'identifier.value':'value',
                 'identifier.image_id':'image_id',
                 'identifier.permalink':'permalink',
                 'identifier.entity_def_id':'entity_def_id'}

order = ['Grant','Pre Seed Round','Seed Round','Series A','Series B','Series C',
         'Series D','Series E','Series F','Series G','Series H','Series I',
         'Series J','Series K','Secondary Market','Private Equity Round',
         'Debt Financing','Angel Round','Funding Round','Venture Round',
         'Corporate Round','Non Equity Assistance', 'Convertible Note', 'Post-IPO Equity','']

order_abbrev = ['Grant','Pre Seed', 'Seed','A','B','C','D','E','F','G','H','I','J','K',
                'Secondary','Private Eq', 'Debt', 'Angel Rnd', 'Funding Rnd',
                'Venture Rnd', 'Corporate Rnd', 'Non Equity Assist', 'Convert Note',
                'Post-IPO Equity','']

abbrev_mapper = dict(zip(order,order_abbrev))
order_mapper = {key:i for i,key in enumerate(order)}

def url_count(query, query_type):
    '''
    Return the total number of results of a query.

    Parameters
    ------------
    query : json
        Input query.
    query_type : str
        One of the types of accepted Crunchbase API searches:
        organizations, people, funding_rounds, acquisitions, investments, events, press_references,
        funds, event_appearances, ipos, ownerships, categories, category_groups, locations, jobs,
        key_employee_changes, addresses, degrees, principals

    Return
    ------------
    count : int
        Count of results.
    '''
    # POST method with Crunchbase API URL and query_type as a parameter, and passing query as json.
    r = requests.post('https://api.crunchbase.com/api/v4/searches/'+query_type,params=userkey,json=query)
    count = json.loads(r.text)['count']
    return count

def url_extraction(query, query_type, raw):
    '''
    Return the results for a query, deserialize to a Python dictionary object, and transform into pandas DataFrame.
    * Appends the results of the query to the global dataframe variable, raw

    Parameters
    ------------
    query : json
        Input query.
    query_type : str
        One of the types of accepted Crunchbase API searches:
        organizations, people, funding_rounds, acquisitions, investments, events, press_references,
        funds, event_appearances, ipos, ownerships, categories, category_groups, locations, jobs,
        key_employee_changes, addresses, degrees, principals
    '''
    # Create global raw variable. This ensures that it can be updated if the API call needs to loop.
    # POST method with API URL, query_type as a parameter, and passing query as json.
    r = requests.post('https://api.crunchbase.com/api/v4/searches/'+query_type, params=userkey, json=query)
    # Return results of query
    result = json.loads(r.text)
    # Normalize semi-structured JSON data into a flat table, forcing it to fit into a relational data structure.
    try:
        normalized_raw = json_normalize(result['entities'])
    except TypeError:
        error_string = 'From Crunchbase -- CODE {}: {}'.format(result[0]['code'].upper(),result[0]['message'].upper())
        raise TypeError(error_string)
    # Append normalized entity results to global raw variable
    raw = raw.append(normalized_raw, ignore_index=True)
    return raw

def go_past_1000(query, query_type, count, raw):
    '''
    This sets up a while loop to go past the Crunchbase API POST limit of returning only 1000 results.
    * While loop continues until it reaches the total result count.
    * Appends the results of each loop to the global dataframe variable, raw.

    Parameters
    ------------
    query : json
        Input query.
    query_type : str
        One of the types of accepted Crunchbase API searches:
        organizations, people, funding_rounds, acquisitions, investments, events, press_references,
        funds, event_appearances, ipos, ownerships, categories, category_groups, locations, jobs,
        key_employee_changes, addresses, degrees, principals
    count : int
        Value output from url_count function
    '''
    # Query loop starts
    data_acq = 0
    while data_acq < count:
        if data_acq != 0:
            # Selects the most recently added result
            last_uuid = raw.uuid[len(raw.uuid)-1]
            # Saves most recent uuid query so POST request starts after this one
            query['after_id'] = last_uuid
            # Extracts data
            raw = url_extraction(query, query_type, raw)
            # Updates data_acq variable
            data_acq = len(raw.uuid)
        else:
            # Removes after_id in case its there before the query starts.
            if 'after_id' in query:
                query = query.pop('after_id')
                # Extracts data
                raw = url_extraction(query, query_type, raw)
                # Updates data_acq variable
                data_acq = len(raw.uuid)
            # Starting query loop
            else:
                # Extracts data
                raw = url_extraction(query, query_type, raw)
                # Updates data_acq variable
                data_acq = len(raw.uuid)
    return raw

def autocompletes(search_input, collection_ids=None, limit=10, verbose=False):
    '''
    Suggests matching Identifier entities based on the query and entity_def_ids provided.

    Parameters
    ------------
    search_input : str
        Value to perform the autocomplete search with.
    collection_ids : list
        * A comma separated list of collection ids to search against.
        * Leaving this blank means it will search across all identifiers.
        * Entity defs can be constrained to specific facets by providing them as facet collections.
        * Accepted collection ids: organizations, people, funding_rounds, acquisitions,
        investments, events, press_references, funds, event_appearances, ipos, ownerships,
        categories, category_groups, locations, jobs
    limit : int, default=10
        Number of results to retrieve; default=10, max=25

    Return
    ------------
    dataframe : pandas.core.frame.DataFrame
        Results of autocompletes query as pandas DataFrame
    '''
    if type(collection_ids)!=list and type(collection_ids)==str:
        collection_ids = [collection_ids]
    # Create parameter dictionary to pass into POST method
    params = {**userkey, 'query':search_input}
    # Add input collection ids to parameters dictionary
    if collection_ids and type(collection_ids)==list:
        params.update({'collection_ids':','.join(collection_ids)})
    # Add input limit to parameters dictionary
    if limit and type(limit)==int:
        params.update({'limit':limit})
    # POST method with API URL, query_type as a parameter, and passing query as json.
    r = requests.get('https://api.crunchbase.com/api/v4/autocompletes', params=params)
    # Return results of query
    result = json.loads(r.text)['entities'][0]
    # Normalize semi-structured JSON data into a flat table, forcing it to fit into a relational data structure.
    #normalized_result = json_normalize(result['entities'])
    # Return results of autocompletes query as pandas dataframe
    uuid = result['identifier']['uuid']
    value = result['identifier']['value']
    # Print statements
    if verbose:
        descript = result['short_description']
        print('Searching for {}'.format(search_input.upper()))
        print('*'*50)
        print('Found {} !!!!!!!\nDescription: {}\n'.format(value.upper(),descript))
    return uuid, value

def primary_info(person_id, field_ids=['primary_job_title','primary_organization','linkedin'], card_ids=None):
    '''
    Get one person's primary job title, organization, and LinkedIn url from Crunchbase.

    Parameters
    ------------
    person_uuid : str
        uuid or permalink of individual
    field_ids : list
        *Crunchbase fields to include on the resulting entity, either an array of
        field_id strings in JSON or a comma-separated list encoded as string
    card_ids : int, default=None
        * Crunchbase card ids to include on the resulting entity, as an array of card_id
        strings in JSON encoded as a string
        * Card ids for Person: degrees, event_appearances, fields, founded_organizations, jobs,
        participated_funding_rounds, participated_funds, participated_investments, partner_funding_rounds,
        partner_investments, press_references, primary_job, primary_organization

    Return
    ------------
    {uuid:name} : dict
        Dictionary mapper of uuid to the individual's full name
    {uuid:title} : dict
        Dictionary mapper of uuid to the individual's primary job title
    {uuid:org} : dict
        Dictionary mapper of uuid to the individual's primary organization name
    {uuid:org_uuid} : dict
        Dictionary mapper of uuid to the individual's primary organization uuid
    {uuid:linkedin} : dict
        Dictionary mapper of uuid to the individual's LinkedIn

    '''
    # Create parameter dictionary to pass into POST method
    params = {**userkey}
    # Add input field ids to parameters dictionary
    if field_ids and type(field_ids)==list:
        params.update({'field_ids':','.join(field_ids)})
    # Add input cards ids to parameters dictionary
    if card_ids and type(card_ids)==list:
        params.update({'card_ids':','.join(card_ids)})
    # POST method with API URL, query_type as a parameter, and passing query as json.
    r = requests.get('https://api.crunchbase.com/api/v4/entities/people/'+person_id, params=params)
    # Return results of query
    result = json.loads(r.text)
    # Pull uuid of searched individual
    uuid = result['properties']['identifier']['uuid']
    name = result['properties']['identifier']['value']
    # Pull LinkedIn URL from json results (if it exists)
    try:
        linkedin = result['properties']['linkedin']['value']
    except KeyError:
        linkedin = 'NA'
    # Pull primary job title from json results (if it exists)
    try:
        title = result['properties']['primary_job_title']
    except KeyError:
        title = 'NA'
    # Pull primary organization from json results (if it exists)
    try:
        org = result['properties']['primary_organization']['value']
    except KeyError:
        org = 'NA'
    # Pull primary organization uuid from json results (if it exists)
    try:
        org_uuid = result['properties']['primary_organization']['uuid']
    except KeyError:
        org_uuid = 'NA'
    return {uuid:name}, {uuid:title}, {uuid:org}, {uuid:org_uuid}, {uuid:linkedin}

def primary_info_of_people(person_uuids):
    # Start with empty dictionnaries
    all_names = {}
    all_titles = {}
    all_orgs = {}
    all_orgs_uuid = {}
    all_linkedin = {}
    no_primary_info = []
    # For each API call, update dictionary if it's not empty
    i = 0
    print('Count of primary_info API calls, number of unique individuals found in query:')
    while i < len(person_uuids):
        print(i+1, end=' ')
        person = person_uuids[i]
        try:
            # API Call
            name,primary_job_title,primary_org,primary_org_uuid,linkedin = primary_info(person)
            all_names.update(name)
            # Update job title dictionary as long as its not equal to 'NA'
            if primary_job_title[person] != 'NA':
                all_titles.update(primary_job_title)
            # Update organization dictionary as long as its not equal to 'NA'
            if primary_org[person] != 'NA':
                all_orgs.update(primary_org)
            # Update organization dictionary as long as its not equal to 'NA'
            if primary_org_uuid[person] != 'NA':
                all_orgs_uuid.update(primary_org_uuid)
            # Update LinkedIn dictionary as long as its not equal to 'NA'
            if linkedin[person] != 'NA':
                all_linkedin.update(linkedin)
            # If any are equal to 'NA', store in no_primary_info list for safekeeping.
            if primary_job_title[person] == 'NA' or primary_org[person] == 'NA' or linkedin[person] == 'NA' or primary_org_uuid[person] =='NA':
                no_primary_info.append(person)
            # Continue looping
            i += 1
        except JSONDecodeError:
            print('[From Crunchbase: Usage limit exceeded. Pause for 5 seconds and continue.]',end =' ')
            time.sleep(5)
    # Count of how many are missing Title, Organization, or LinkedIn
    print('\n\n{} out of {} records are missing either a primary job title, primary organization, or LinkedIn url.\n'.format(len(no_primary_info),i))
    return all_names, all_titles, all_orgs, all_orgs_uuid, all_linkedin

def create_board_strings(lst_of_frames, company_names):
    # For saving to csv
    all_dict = []
    for df in lst_of_frames:
        # Fill in affiliation dictionary
        people_dict = {}
        # For each company
        for org in company_names:
            # Filter df to unique company affiliations
            temp_df = df[df['company']==org]
            # Collapse individual names to list
            names = temp_df['person'].to_list()
            # Collapse individual organizations to list
            companies = temp_df['primary_org'].to_list()
            # Start with empty string
            board_string = ''
            # Exclude if there are no individuals affiliated
            if names != []:
                # Make temp dictionary of name:org
                board_info = dict(zip(names, companies))
                # Add them to string
                for name, company in sorted(board_info.items()):
                    # If individual does not have a primary organization
                    if pd.isna(company):
                        board_string += name +'; '
                    # If individual has a primary organziation, place into parentheses
                    else:
                        board_string += name+' ('+company+'); '
                # Remove trailing semicolon and remove extra commas
                board_string = board_string[:-2].replace(',', '')
            # Add string to main dictionary
            people_dict[org] = board_string
        all_dict.append(people_dict)
    return all_dict

def create_investor_strings(frame):
    all_investors = {}
    for co in frame.company.unique():
        investor_str = ''
        # Create sub-DF with just the company's investors
        co_df = frame[frame['company']==co]
        # Turn into list
        co_investors = sorted(list(set(co_df['investor_name'].to_list())))
        for inv in co_investors:
            # Add investor to string
            investor_str += inv+'; '
        # Remove trailing semicolon
        investor_str = investor_str[:-2]
        all_investors[co] = investor_str

    all_investors_w_info = {}
    for co in frame.company.unique():
        investor_str = ''
        # Create sub-DF with just the company's investors
        co_df = frame[frame['company']==co]
        # Create unique list of investment types
        lst = list(set(co_df['type'].to_list()))
        lst = sorted(lst, key=lambda d:order_mapper[d])
        for item in lst:
            # Create sub-list of investors with a particular investment type
            investor_type_lst = sorted(list(set(co_df['investor_name'][co_df['type']==item].to_list())))
            if investor_type_lst != []:
                # Add investment type to string
                investor_str += item + ' ('
                for com in investor_type_lst:
                    # Add investor to string
                    investor_str += com + '; '
                # Remove trailing semicolon and add end parenthesis
                investor_str = investor_str[:-2]
                investor_str += ') | '
        # Remove trailing characters
        investor_str = investor_str[:-3]
        all_investors_w_info[co] = investor_str
    return all_investors, all_investors_w_info


def whoKnows(name, df, person_first=True):
    '''
    This function takes in a name string and a dataframe generated by the url_extraction(query, "jobs") function.

    Returns a string that is a concatenated list of unique names mapped to their companies, excluding the rows of the named person.

    This is a Pledge 1% action that helps us see who knows a specific Boardroom Ally and how, pulled from the Boardroom Allies affiliations dataframe.

    If person_first is True (default), the output will aggregate by person.
    matches_str = 'Name1 (Company1, Company), Name2 (Company2), Name3 (Company1), ...'

    If person_first is False, the output will aggregate by company
    matches_str = 'Company1 (Name1, Name2, Name3), Company2 (Name1), Company3 (Name2, Name3), ...'
    '''
    # Don't start if the input name search comes up with nothing.
    if df["properties.organization_identifier.value"][df["properties.person_identifier.value"] == name] is None:
        return "There's no one in this list by that name. Check for typos!"
    # Make a list of all unique companies affiliated with input name
    company_matches = set(df["properties.organization_identifier.value"][df["properties.person_identifier.value"] == name].to_list())
    # Create matches dataframe, filtering by those that match the unique company list.
    matches_df = df[df["properties.organization_identifier.value"].isin(company_matches)]
    # Remove the person from the results, to remove situations like: "Byron Deeter" knowing "Byron Deeter"
    matches_df = matches_df[matches_df["properties.person_identifier.value"] != name].sort_values(["properties.organization_identifier.value"])
    # Create intermediate dictionary which will de-dupe based on `person_first` value
    person_matches = matches_df["properties.person_identifier.value"].to_list()
    company_matches = matches_df["properties.organization_identifier.value"].to_list()
    matches_dict = {}
    if person_first:
        # Aggregate by name.
        for i in range(len(person_matches)):
            # If person already in dictionary
            if person_matches[i] in matches_dict.keys():
                # Append company to list
                matches_dict[person_matches[i]].append(company_matches[i])
            else:
                # Add person to dictionary
                matches_dict[person_matches[i]] = [company_matches[i]]
    if not person_first:
        # Aggregate by company.
        for i in range(len(person_matches)):
            # If company already in dictionary
            if company_matches[i] in matches_dict.keys():
                # Append person to list
                matches_dict[company_matches[i]].append(person_matches[i])
            else:
                # Add company to dictionary
                matches_dict[company_matches[i]] = [person_matches[i]]
    # Create output string
    matches_str = ""
    for key, value in matches_dict.items():
        # Start returned string
        matches_str += key + " ("
        # Start empty string for loop
        forloop_str = ""
        for i, item in enumerate(matches_dict[key]):
            if i == len(matches_dict[key]) - 1:
                forloop_str += item + ")"
                continue
            forloop_str += item + ", "
        matches_str += forloop_str + ", "
    # Remove extra space and comma
    matches_str = matches_str[:-2]
    return matches_str
