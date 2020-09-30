import pandas as pd

hcis_codes = {'175015' : 'Non grant related expenses',
'175038' : 'Realytics services for NJII clients',
'380D17' : 'Do not use this index',
'382F21' : '2016 and 2017 program onboarding',
'382F22' : '2017 Onboarding Milestone program',
'382F23' : 'NJIIS',
'382F24' : 'emPOLST project',
'382F25' : 'Consumer access project',
'382F26' : 'Consent management project',
'382F27' : '2016 Onboarding Milestone program',
'382F28' : 'Perinatal Risk Assessment or PRA registry proejct',
'382F29' : 'MPP program (Core index)',
'382F30' : 'MPP program (Milestone index)',
'382M01' : 'NJHIN management (please do not use this unless indicated by Jen)',
'382M02' : 'SUD program (Core index)',
'382M03' : 'SUD program (Milestone index)',
'382M04' : 'Lead registry project',
'382M05' : 'Contact tracing (CDRSS project)',
'104000' : 'HCIS non service line related index for NJII employees',
'104010' : 'MIPS index for NJII employees',
'104040' : 'DSRIP index for NJII employees',
'104050' : 'Aetna index for NJII employees',
'104060' : 'Relytics index for NJII employees'}

hcis_codes = pd.DataFrame(hcis_codes.items(), columns = ['Index', 'Description']) 
print(hcis_codes)