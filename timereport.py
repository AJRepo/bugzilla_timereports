#!/usr/bin/env python3
"""
This queries bugzilla and creates a time summary or invoice
based on work done and recorded in bugzilla

This work is licensed under the GNU GPLv2
This work is copyright 2020 by AJRepo, https://github.com/AJRepo
"""

import sys
import getopt
import datetime
import urllib
import textwrap
from dateutil.parser import parse
import bugzilla


class BugzillaTimeSummary:
    """Bugzilla Time Summary Class"""
    def __init__(self, sys_args):

        #Eventually support multiple products, now just one
        #self.args = sys_args  #pass args to Class variable
        self.debug = False
        self.begin_date = ""
        self.end_date = ""
        self.setup_args(sys_args)

        self.check_begin_date()
        self.check_end_date()

        #set start and end dates
        if  self.end_date == "":
            self.print_v("dates not set or = last_month", self.end_date)
            self.set_timeperiod_lastmonth()

        worktime = self.calulate_worktime()

        self.print_v("Worktime=", worktime)
        if self.invoice:
            self.generate_invoice(worktime)
        else:
            self.print_v("Not generating invoice", self.invoice)

    @staticmethod
    def print_usage():
        """Print the Usage of the program as help text"""
        print("Usage:\n timereport.py [Arguments]\n")
        print("Arguments:")
        print("  [-d]              [--debug]                    Turn on debugging messages")
        print("  [-p <product>]    [--product=<product>]        Quote if product has spaces")
        print("  [-r <#>]          [--rate=<#>]                 Invoice rate per hour")
        print("  [-s]              [--show_assigned_to]         Show users in bug report")
        print("  [-w]              [--wrap_long]                Wrap long lines")
        print("  [-i]              [--invoice]                  Print an invoice using --rate")
        print("  [-e <YYYY-MM-DD>] [--end_date=<YYYY-MM-DD>]    End Date")
        print("  [-b <YYYY-MM-DD>] [--begin_date=<YYYY-MM-DD>]  Begin Date")
        print(" ")
        print("    If only --begin_date is set, then --end_date defaults to today")
        print("    If both --begin_date and --end_date are unset, then defaults to last month")

    def setup_args(self, args):
        """Setup parameters from command line"""
        #setup the defaults
        self.debug = False
        self.invoice = False
        self.show_assigned_to = False
        self.products = ""
        self.begin_date = ""
        self.end_date = ""
        self.rate = float(0)
        self.wrap = False
        rate_set = False
        bold = '\033[1m'
        reset = '\033[0m'

        #If need args uncomment below and replace _ with args
        #args = []
        opts = []
        try:
            opts, _ = getopt.getopt(args,
                                    "dp:r:swib:e:",
                                    ["debug", "product=", "rate=", "invoice",
                                     "show_assigned_to", "begin_date=", "end_date=",
                                     "begin-date=", "end-date=",
                                     "wrap_long"]
                                   )
        except getopt.GetoptError:
            self.print_usage()
            sys.exit(2)

        for opt, arg in opts:
            if opt in ("-d", "--debug"):
                self.debug = True
            elif opt in "--end-date":
                print(f"\nError: {bold}underscore{reset}, not hyphens. end-date -> end_date\n")
                self.print_usage()
                sys.exit(2)
            elif opt in "--begin-date":
                print(f"\nError: {bold}underscore{reset}, not hyphens. begin-date -> begin_date\n")
                self.print_usage()
                sys.exit(2)
            elif opt in ("-b", "--begin_date"):
                self.begin_date = str(arg)
            elif opt in ("-e", "--end_date"):
                self.end_date = str(arg)
            elif opt in ("-p", "--product"):
                self.products = str(arg)
            elif opt in ("-r", "--rate"):
                self.rate = float(arg)
                rate_set = True
            elif opt in ("-s", "--show_assigned_to"):
                self.show_assigned_to = True
            elif opt in ("-w", "--wrap_long"):
                self.wrap = True
            elif opt in ("-i", "--invoice"):
                self.invoice = True

        #I suppose we could check if invoice=True and rate="" here
        if not rate_set and self.invoice:
            print("Error: Invoice option chosen but rate not set")
            print("       Use --rate=<float> if using invoicing.")
            print("       Exiting.")
            sys.exit(1)



    def check_begin_date(self):
        """ make sure dates are date objects """
        #If begin_date is not set - make it today
        if self.begin_date == "this_month" or self.begin_date == "":
            self.begin_date = datetime.datetime.today().replace(day=1, hour=00, minute=00)
        elif self.begin_date == "last_month":
            self.set_timeperiod_lastmonth()
        else:
            self.begin_date = parse(self.begin_date)

    def check_end_date(self):
        """ make sure dates are date objects """
        #If end_date is not set - make it the end of today
        if self.end_date == "":
            self.end_date = datetime.datetime.today().replace(hour=23, minute=59, second=59)
        else:
            self.end_date = parse(self.end_date)

    def print_v(self, msg, var):
        """ Print if debug is true """
        if self.debug:
            print(msg, var)

    def generate_invoice(self, worktime):
        """Generate an invoice
            Note: Default rate = 0.00
        """

        #total = self.rate * worktime

        print('------------------------------------------------------------')
        print(
            f"{'Item':^11}:"
            f"{'Description':^39}:"
            f"{'Quantity':^11}:"
            f"{'Rate':^12}:"
            f"{'Amount':^10}")
        print(
            f"{'Consulting':<11}:"
            f" Tickets from {self.begin_date:%Y-%m-%d} to {self.end_date:%Y-%m-%d} :"
            f"{worktime:6.2f} hrs :"
            f" ${self.rate:6.2f}/hr :"
            f"  ${self.rate * worktime:>7.2f}")

    def set_timeperiod_lastmonth(self):
        """set the start and end times for these calculations"""
        tmp_date = datetime.date.today().replace(day=1)
        #end date = last day of last month
        self.end_date = tmp_date - datetime.timedelta(days=1)
        #begin date = first day of last month
        self.begin_date = self.end_date.replace(day=1)

    def calulate_worktime(self):
        """
        Function for generating time worked on bugs a report that
        is generally found at /summarize_time.cgi.
        """

        #Set by get_timeperiod_lastmonth()
        if self.begin_date == "" or self.end_date == "":
            print("Error in setting dates")
            sys.exit(1)


        #print(TMP_DATE)

        self.print_v("Begin Date:", self.begin_date)
        self.print_v("End Date:", self.end_date)
        #base_url = "https://bugzilla.example.com"
        #NOTE: Must NOT have a / at the end of the base_url

        #Look in a .bugzillatc file
        base_url = bugzilla.Bugzilla.get_rcfile_default_url()

        self.print_v("Connecting to: ", base_url)

        if base_url is None or base_url == "":
            print("Error in getting URL. Is your .bugzillarc file setup? ")
            print("Do you have something in that file like")
            print("[DEFAULT]")
            print("url=https://www.example.com")
            print("api_key=your_api_key_here")
            sys.exit(2)

        #If you don't have a ~/.bugzillarc file then you'll have to have an API key
        #api_key = input("Enter Bugzilla API Key: ")

        try:
            #bzapi = bugzilla.Bugzilla(url=base_url, api_key=api_key)
            bzapi = bugzilla.Bugzilla(url=base_url)
        except TimeoutError:
            print("Timeout in creating connection to", base_url)
        except TypeError:
            print("Error in type connection to", base_url)

        if not bzapi.logged_in:
            print("Error: Not Logged in. Lookup API/cached credentials for %s" % base_url)
            print("  Try creating a .bugzillarc file with the following information in it")
            print("    [%s]" % base_url)
            print("    url=%s" % base_url)
            print("    user=<your username>")
            print("    api_key=<the api key you get at %s/userprefs.cgi?tab=apikey>" % base_url)
            sys.exit(0)
        #assert bzapi.logged_in

        worktime = self.calculate_worktime(bzapi, base_url)

        return worktime

    def pretty_print_bug(self, bug, id_width):
        """
        Format a bug line suitable for a time report
        id_width is the space given for the bugid in printing
        """

        #print("AAAAAA = ", bug.total_hours_this_period)
        first_line = True
        space = " "
        summary_width = 40
        if self.wrap and len(bug.summary) > 0:
            summary_list = textwrap.wrap(bug.summary,
                                         width=summary_width,
                                         subsequent_indent="  "
                                        )
        else:
            summary_list = [bug.summary]
        if self.show_assigned_to:
            for summary in summary_list:
                if first_line:
                    print(f"#{bug.id:<{id_width}} : "
                          f"{bug.assigned_to:<36} : "
                          f"{bug.status:<15} : "
                          f"{summary}"
                          )
                    first_line = False
                else:
                    print(f" {space:<{id_width}} : {space:<36} : {space:<15} : {summary}")
        else:
            for summary in summary_list:
                #print(f"#{bug.id:<5} : {bug.status:<15} : {bug_summary}")
                if first_line:
                    print(f"#{bug.id:<{id_width}} : {bug.status:<15} : {summary}")
                    first_line = False
                else:
                    print(f" {space:<{id_width}} : {space:<15} : {summary}")

    def add_historical_time(self, raw_bug_history, begin_date, end_date):
        """
        Given historical data, add up all work done between two dates
        """
        total_time = 0
        for history_items in raw_bug_history:
            #type=dict
            #print("BAZ=", history_items)
            #print("TYPEBAZ=", type(history_items))
            #print("LENBAZ=", len(history_items))
            #history_items = [history, id (bugid), alias]
            for key, value in history_items.items():
                if key == 'history':
                    #print("BAZHIST=", key, value)
                    #print("BAZHISTTYPE=", type(value))
                    for history_entry in value:
                        #print("HHH=", history_entry)
                        #print("DDD=", history_entry['when'])
                        if (history_entry['changes'][0]['field_name'] == 'work_time' and
                                begin_date < parse(str(history_entry['when'])) < end_date
                           ):
                            this_time = float(history_entry['changes'][0]['added'])
                            self.print_v("THISTIME=", this_time)
                            self.print_v("THIS DATE", history_entry['when'])
                            self.print_v("THIS DATE", parse(str(history_entry['when'])))
                            total_time += this_time
                        else:
                            self.print_v("BEGIN DATE", begin_date)
                            self.print_v("NOT THIS DATE", history_entry['when'])
                            self.print_v("END DATE", end_date)
        return total_time

    def calculate_worktime(self, bzapi, base_url):
        """
        Given a start and end date find work done in that time range
        """

        #Currently we limit to just one product, eventually expand to multiple ones
        product = self.products

        if product == "":
            query_product = ""
        else:
            query_product = "&product=" + urllib.parse.quote(product)

        chfields = ("&chfield=%5BBug%20creation%5D&chfield=assigned_to" +
                    "&chfield=cclist_accessible&chfield=component" +
                    "&chfield=deadline&chfield=everconfirmed" +
                    "&chfield=rep_platform&chfield=remaining_time&chfield=work_time" +
                    "&chfield=estimated_time&chfield=op_sys&chfield=priority&chfield=product" +
                    "&chfield=qa_contact&chfield=reporter_accessible&chfield=resolution" +
                    "&chfield=bug_severity&chfield=bug_status&chfield=short_desc&" +
                    "chfield=target_milestone&chfield=bug_file_loc&chfield=version" +
                    "&chfield=votes&chfield=status_whiteboard&"
                    )

        q_url = (base_url + "/buglist.cgi"
                 + "?chfieldfrom=" + str(self.begin_date)
                 + "&chfieldto=" + str(self.end_date)
                 + str(chfields)
                 + str(query_product)
                 + "&query_format=advanced")
        #+ "&query_based_on=BillingSearch")
        #+ "&known_name=BillingSearch&list_id=5188" + str(query_product)
        #+ "&list_id=5188"


        query = bzapi.url_to_query(q_url)

        # Query does have work_time, but is returned blank by the API
        # self.print_v("QUERY=", query)

        bugs = bzapi.query(query)

        num_bugs = len(bugs)

        #self.print_v("RAW BUGS=", bugs)
        self.print_v("BUGS TYPE=", type(bugs))
        i = 0
        list_of_bugs = ""
        id_width = 3

        total_time = 0

        print(f"Time Summary from {self.begin_date:%Y-%m-%d} to {self.end_date:%Y-%m-%d}")
        print('------------------------------------------------------------')

        while i < num_bugs:
            #We don't want total hours worked, just total hours for just this time period
            #We store them in the bugs object which could be dangerous so have a long name
            bugs[i].total_hours_this_period = 0
            self.print_v("DIR=", dir(bugs[i]))
            self.print_v("BUG TYPE", type(bugs[i]))
            #self.print_v("WORK ", bugs[i].work_time)
            if self.debug:
                print(bugs[i])
            self.print_v("BUGFIELDS", bugs[i].bugzilla.bugfields)
            if len(str(bugs[i].id)) > id_width:
                id_width = len(str(bugs[i].bug_id)) + 1
            raw_bug_history = bugs[i].get_history_raw()['bugs']
            #print("TYPE=", type(raw_bug_history))
            #print("LEN=", len(raw_bug_history))
            #print(i, "=", raw_bug_history)
            total_time = self.add_historical_time(raw_bug_history, self.begin_date, self.end_date)
            bugs[i].total_hours_this_period = total_time

            #Print this bug
            self.print_v("TIME=", bugs[i].total_hours_this_period)
            self.pretty_print_bug(bugs[i], id_width)
            list_of_bugs = str(list_of_bugs) + str(bugs[i].id)
            #Iterate to next bug
            i += 1
            if i < num_bugs:
                list_of_bugs += ","

        self.print_v("LIST OF BUGS=", list_of_bugs)
        self.print_v("TOTAL TIME=", total_time)

        #for bug in bugs:
        #    list_of_bugs += bug.id + ","

        #report_url = (base_url + "/summarize_time.cgi" +
        #              "?start_date=" + str(begin_date) +
        #              "&end_date=" + str(end_date) +
        #              "&group_by=number" +
        #              "&id=" + list_of_bugs +
        #              "&do_report=1")
        #
        #print("this tries to replicate report", report_url)
        #query = bzapi.url_to_query(report_url)
        #print(query)

        return total_time

if __name__ == "__main__":
    #calulate_worktime()
    INSTA = BugzillaTimeSummary(sys.argv[1:])
