def makequery_investors(uuid_lst, limit=1000):
    '''
    Create query for an investments search: Investors of input companies
    * Organization includes list of organization uuid values

    Parameters
    ------------
    uuid_lst : array_list
        Input list.
    limit : int, optional
        'Limit' paramter. 1000, the default value, is the maximum number of results.

    Return
    ------------
    query : dictionary
        Query as json.
    '''
    if type(uuid_lst)!=list and type(uuid_lst)==str:
        uuid_lst = [uuid_lst]
    query = {'field_ids':['name','investor_identifier','organization_identifier','partner_identifiers'],
             'limit':limit,
             'query':[{'type':'predicate','field_id':'organization_identifier','operator_id':'includes','values':uuid_lst}]
            }
    return query

def makequery_board_affiliations(uuid_lst, limit=1000):
    '''
    Create query for a jobs search: Board Affiliations
    * Organization includes list of organization uuid values
    * Excludes employee- and executive-level jobs

    Parameters
    ------------
    uuid_lst : array_list
        Input list.
    limit : int, optional
        'Limit' paramter. 1000, the default value, is the maximum number of results.

    Return
    ------------
    query : dictionary
        Query as json.
    -
    '''
    if type(uuid_lst)!=list and type(uuid_lst)==str:
        uuid_lst = [uuid_lst]
    query = {'field_ids':['entity_def_id','identifier','job_type','name','organization_identifier',
                            'person_identifier','short_description','is_current','title','uuid'],
             'query':[{'type':'predicate','field_id':'organization_identifier','operator_id':'includes','values':uuid_lst},
                      {'type':'predicate','field_id':'job_type','operator_id':'not_includes','values':['employee',
                                                                                                       'executive']}],
             'limit':limit}
    return query

def makequery_jobs(uuid_lst, limit=200):
    '''
    Job Search: Current and Former Board/Executive Affiliations
    - Person includes list of `uuid` values
    - The job title is current (`is_current == True`)
    - Excludes `employee` level jobs
    '''
    if type(uuid_lst)!=list and type(uuid_lst)==str:
        uuid_lst = [uuid_lst]
    query = {'field_ids':['entity_def_id','identifier','job_type','name','organization_identifier',
                            'person_identifier','short_description','is_current','title','uuid'],
            'query': [{'type':'predicate','field_id':'person_identifier','operator_id':'includes','values':uuid_lst},
                    {'type':'predicate','field_id':'job_type','operator_id':'not_includes','values':['employee']}],
            'limit': limit}
    return query

def makequery_org(uuid_lst, limit=1000):
    '''
    '''
    if type(uuid_lst)!=list and type(uuid_lst)==str:
        uuid_lst = [uuid_lst]
    query = {'field_ids': ['name','website_url','founder_identifiers','categories','category_groups',
    'diversity_spotlights','funding_stage','funding_total','funds_total','last_funding_type',
    'last_funding_at','hub_tags','revenue_range','uuid'],
    'limit': limit,
    'query': [{'type': 'predicate','field_id': 'uuid','operator_id': 'includes','values': uuid_lst}]
    }
    return query

def makequery_jobs_board_of_org(uuid_lst, limit=1000):
    '''
    Job Search: Current and Former Board Affiliations
    - Organization includes list of `uuid` values
    - Excludes `employee` and `executive` level jobs
    '''
    if type(uuid_lst)!=list and type(uuid_lst)==str:
        uuid_lst = [uuid_lst]
    query = {'field_ids': ['entity_def_id','identifier','job_type','name','organization_identifier','person_identifier',
            'short_description','is_current','started_on','ended_on','title','updated_at','uuid'],
        'limit': limit,
        'query': [{'type': 'predicate','field_id': 'organization_identifier','operator_id': 'includes','values': uuid_lst},
        {'type': 'predicate','field_id': 'job_type','operator_id': 'not_includes','values': ['employee', 'executive']}]
        }
    return query

def makequery_jobs_exec(uuid_lst, limit=1000):
    '''
    Job Search: Current Executive Roles
    - Person includes list of `uuid` values
    - The job title is current (`is_current == True`)
    - Excludes `employee`, `board_member`, `advisor`, and `board_observer` job types
    '''
    if type(uuid_lst)!=list and type(uuid_lst)==str:
        uuid_lst = [uuid_lst]
    query = {'field_ids': ['entity_def_id','employee_featured_order','identifier','job_type','name',
    'organization_identifier','person_identifier','short_description','is_current','started_on',
    'ended_on','title','updated_at','uuid'],
    'limit': limit,
    'query': [{'type': 'predicate','field_id': 'person_identifier','operator_id': 'includes','values': uuid_lst},
    {'type': 'predicate','field_id': 'is_current','operator_id': 'eq','values': ['true']},
    {'type': 'predicate','field_id': 'job_type','operator_id': 'not_includes','values': ['employee', 'board_member', 'advisor', 'board_observer']}]
    }
    return query
