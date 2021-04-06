# bugzilla_timereports

Is built to use Python-Bugzilla Tools (https://github.com/python-bugzilla/python-bugzilla) to generate time reports and invoices.

Requires Python 3 and that library. 

If you use the --invoice flag then you also have to specify the --rate flag. 

```
Usage:
 timereport.py [Arguments]

Arguments:
  [-d]              [--debug]                    Turn on debugging messages
  [-p <product>]    [--product=<product>]        Quote if product has spaces
  [-r <#>]          [--rate=<#>]                 Invoice rate per hour
  [-s]              [--show_assigned_to]         Show users in bug report
  [-w]              [--wrap_long]                Wrap long lines
  [-i]              [--invoice]                  Print an invoice using --rate
  [-e <YYYY-MM-DD>] [--end_date=<YYYY-MM-DD>]    End Date
  [-b <YYYY-MM-DD>] [--begin_date=<YYYY-MM-DD>]  Begin Date
 
    If only --begin_date is set, then --end_date defaults to today
    If both --begin_date and --end_date are unset, then defaults to last month
```

See https://github.com/python-bugzilla/python-bugzilla for the creation of the .bugzillarc file. 
If you setup the bugzilla user to limit access to a particular product then you don't have to 
also specify --product. 

To setup a user and use the API key (recommended)

1. Create a user
2. Setup that user's permissions
3. Impersonate that user
4. As that user. create an API key for that user ( /userprefs.cgi?tab=apikey ) 
5. Create the .bugzillarc file with that user's API key 

