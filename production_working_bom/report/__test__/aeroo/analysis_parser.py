# -*- coding: utf-8 -*-
###############################################################################
#
#    Copyright (C) 2001-2014 Micronaet SRL (<http://www.micronaet.it>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
from openerp.report import report_sxw
from openerp.report.report_sxw import rml_parse

class Parser(report_sxw.rml_parse):    
    def __init__(self, cr, uid, name, context):
        self.context = context
        super(Parser, self).__init__(cr, uid, name, context)
        self.localcontext.update({
            'get_objects': self.get_objects,
        })

    def get_objects(self, ):
        ''' Return list of days
        '''
        # Query for list
        self.cr.execute("""
            SELECT DISTINCT left(CAST(date_planned AS TEXT), 10) as day
            FROM mrp_production_workcenter_line
            ORDER BY day;
            """)
        res = []
        for day in self.cr.fetchall():
            day = day[0]
            start = "%s 00:00:00" % day
            end = "%s 23:59:59" % day
            
            self.cr.execute("""
                SELECT rr.name, q.hour, q.workers 
                FROM (
                    SELECT 
                        workcenter_id AS wc, 
                        sum(hour) AS hour, 
                        min(workers) AS workers 
                    FROM mrp_production_workcenter_line 
                    WHERE date_planned >= %s and date_planned <= %s 
                    GROUP BY workcenter_id, workers) AS q 
                    
                    JOIN mrp_workcenter wc ON (q.wc = wc.id) 
                    JOIN resource_resource rr ON (wc.resource_id = rr.id) 
                    ORDER BY rr.name;
                """, (start, end))
            activity = []
            for record in self.cr.fetchall():
                activity.append(record)
            res.append((day, activity))
            print res
        return res

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
