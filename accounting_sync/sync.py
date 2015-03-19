# -*- coding: utf-8 -*-
###############################################################################
#
# OpenERP, Open Source Management Solution
# Copyright (C) 2001-2015 Micronaet S.r.l. (<http://www.micronaet.it>)
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################

import os
import sys
import logging
import openerp
import xmlrpclib
import openerp.netsvc as netsvc
import openerp.addons.decimal_precision as dp
from openerp.osv import fields, osv, expression, orm
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from openerp import SUPERUSER_ID, api
from openerp import tools
from openerp.tools.translate import _
from openerp.tools.float_utils import float_round as round
from openerp.tools import (DEFAULT_SERVER_DATE_FORMAT, 
    DEFAULT_SERVER_DATETIME_FORMAT, 
    DATETIME_FORMATS_MAP, 
    float_compare)


_logger = logging.getLogger(__name__)

class res_company(orm.Model):
    ''' Add XMLRPC parameters for connections
    '''

    _inherit = 'res.company'
    
    # Utility:
    def get_xmlrpc_socket(
            self, cr, uid, company_id=False, context=None):
        ''' Read element with company_id or passed 
        '''
        if not company_id:
            company_id = self.search(cr, uid, [], context=context)[0]
        elif type(company_id) in (list, tuple):
            company_id = company_id[0]
        
        parameters = self.browse(cr, uid, company_id, context=context)

        try:
            xmlrpc_server = "http://%s:%s" % (
                mx_parameter_server,
                mx_parameter_port,
            )
            return xmlrpclib.ServerProxy(xmlrpc_server)
        except:
            raise osv.except_osv(
                _('Import CL error!'),
                _(
                'XMLRPC for calling importation is not response check'
                ' if program is open on XMLRPC server'), )
        
    _columns = {
        'accounting_sync_host': fields.char(
            'Accounting sync XMLRPC host', 
            size=64, 
            required=False, 
            readonly=False, 
            help="IP address: 10.0.0.2  or hostname: server.example.com"),
        'accounting_sync_port': fields.integer(
            'Acounting sync port', 
            required=False, 
            readonly=False, 
            help="XMLRPC port, example: 8000"),
        }


class MrpProduction(orm.Model):
    ''' Add extra field to manage connection with accounting
    '''
    
    _inherit = 'mrp.production'

    # Override function
    def accounting_sync(self, cr, uid, ids, context=None):
        ''' Read all line to sync in accounting and produce it for 
            XMLRPC call
        '''
        sol_pool = self.pool.get('sale.order.line')
        # Read all line to close
        sol_ids = sol_pool.search(cr, uid, [
            ('sync_state', 'in', ('partial', 'closed'))
            ], 
            order='order_id', # TODO line sequence?
            context=context, )

        # Write in file:
        temp_file = os.path.expanduser(os.path.join('~', 'close.txt'))
        out = open(temp_file, 'w')
        for line in sol_pool.browse(cr, uid, sol_ids, context=context):
            order = line.order_id.name.split("-")[-1].split("/")[0]
            out.write("%1s%-18s%-18s%10s%10sXX\n\r" % ( # TODO
                'P' if line.sync_state == 'partial' else 'T', # Type (part/tot)
                order,                           # Order
                line.product_id.default_code,                 # Code
                int(line.product_uom_maked_qty),              # Q (part/tot)
                line.date_deadline,                           # Deadline
                ))
        out.close()
                
        # XMLRPC call for import the file
        
        return True

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
