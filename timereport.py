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
import bugzilla

class BugzillaTimeSummary:
    """Bugzilla Time Summary Class"""
    def __init__(self, sys_args):

        #Eventually support multiple products, now just one
        self.args = sys_args  #pass args to Class variable
        self.debug = False
        self.products = ""
        self.rate = float(0)
        self.setup_args()

        self.print_v("PRODUCTS=", self.products)

        #set start and end dates
        if self.begin_date == "" and self.end_date == "":
            self.set_timeperiod()

        worktime = self.calulate_worktime()

        self.print_v("Worktime=", worktime)
        if self.invoice:
            self.generate_invoice(worktime)
        else:
            self.print_v("Not generating invoice", self.invoice)

    def setup_args(self):
        """Setup parameters from command line"""
        #setup the defaults
        self.debug = False
        self.invoice = False
        self.show_assigned_to = False
        self.products = ""
        self.begin_date = ""
        self.end_date = ""

        #If need args uncomment below and replace _ with args
        #args = []
        opts = []
        try:
            opts, _ = getopt.getopt(self.args,
                                    "dp:r:sb:e:",
                                    ["debug", "product=", "rate=", "invoice",
                                     "show_assigned_to", "begin_date=", "end_date="]
                                   )
        except getopt.GetoptError:
            print("Usage:\n create_invoice.py [Arguments]\n")
            print("Arguments:")
            print("  [-d]              [--debug]                   Turn on debugging messages")
            print("  [-p <product>]    [--product=<product>]       Quote if product has spaces")
            print("  [-e <YYYY-MM-DD>] [--end_date=<YYYY-MM-DD>]   End Date for Report")
            print("  [-b <YYYY-MM-DD>] [--begin_date=<YYYY-MM-DD>] Begin Date for Report")
            print("  [-r <#>]          [--rate=<#>]                Invoice rate per hour")
            print("  [-s]              [--show_assigned_to]        Show users in bug report")
            print("  [--invoice]                          If set, print an invoice based on --rate")
            sys.exit(2)

        for opt, arg in opts:
            if opt in ("-d", "--debug"):
                self.debug = True
            elif opt in ("-b", "--begin_date"):
                self.begin_date = str(arg)
            elif opt in ("-e", "--end_date"):
                self.end_date = str(arg)
            elif opt in ("-p", "--product"):
                self.products = str(arg)
            elif opt in ("-r", "--rate"):
                self.rate = float(arg)
            elif opt in ("-s", "--show_assigned_to"):
                self.show_assigned_to = True
            elif opt == "--invoice":
                self.invoice = True

        #I suppose we could check if invoice=True and rate="" here
        #print(self.debug, self.products, self.rate)
        #sys.exit(2)

    def print_v(self, msg, var):
        """ Print if debug is true """
        if self.debug:
            print(msg, var)

    def generate_invoice(self, worktime):
        """Generate an invoice"""
        if self.rate == "" or self.rate <= 0:
            print("Error in self.rate", self.rate)
            exit(1)

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
            f"'Tickets from {self.begin_date} to {self.end_date} :"
            f"{worktime:6.2f} hrs :"
            f" ${self.rate:6.2f}/hr :"
            f" ${self.rate * worktime:6.2f}")

    def set_timeperiod(self):
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

        #Set by get_timeperiod()
        if self.begin_date == "" or self.end_date == "":
            print("Error in setting dates")
            exit(1)


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
            exit(2)

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
            print("This example requires cached login credentials for %s" % base_url)
            exit(0)
        #assert bzapi.logged_in
        #assert "asdfasdfa"

        worktime = self.calculate_worktime(bzapi, base_url)

        return worktime

    def pretty_print_bug(self, bug):
        """
        Format a bug line suitable for a time report
        """

        if self.show_assigned_to:
            print(f"#{bug.id:<5} : {bug.assigned_to} : {bug.status:<15} : {bug.summary}")
        else:
            print(f"#{bug.id:<5} : {bug.status:<15} : {bug.summary}")

    def calculate_worktime(self, bzapi, base_url):
        """
        Given a start and end date find work done in that time range
        """

        #Currently we limit to just one product, eventually expand to multiple ones
        product = self.products
        begin_date = self.begin_date
        end_date = self.end_date

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
                 + "?chfieldfrom=" + str(begin_date)
                 + "&chfieldto=" + str(end_date)
                 + str(chfields)
                 + str(query_product)
                 + "&query_format=advanced")
        #+ "&query_based_on=BillingSearch")
        #+ "&known_name=BillingSearch&list_id=5188" + str(query_product)
        #+ "&list_id=5188"


        query = bzapi.url_to_query(q_url)

        #print(query)

        bugs = bzapi.query(query)

        num_bugs = len(bugs)

        #self.print_v("RAW BUGS=", bugs)
        self.print_v("BUGS TYPE=", type(bugs))
        i = 0
        list_of_bugs = ""

        total_time = 0

        print(f"Time Summary from {begin_date} to {end_date}")
        print('------------------------------------------------------------')

        while i < num_bugs:
            self.print_v("BUG TYPE", type(bugs[i]))
            if self.debug:
                print(bugs[i])
            self.print_v("BUGFIELDS", bugs[i].bugzilla.bugfields)
            self.pretty_print_bug(bugs[i])
            list_of_bugs = str(list_of_bugs) + str(bugs[i].id)
            raw_bug_history = bugs[i].get_history_raw()['bugs']
            #print("TYPE=", type(raw_bug_history))
            #print("LEN=", len(raw_bug_history))
            #print(i, "=", raw_bug_history)
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
                                    begin_date < history_entry['when'] < end_date
                               ):
                                this_time = float(history_entry['changes'][0]['added'])
                                self.print_v("THISTIME=", this_time)
                                self.print_v("THIS DATE", history_entry['when'])
                                total_time += this_time
                            else:
                                self.print_v("NOT THIS DATE", history_entry['when'])
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
