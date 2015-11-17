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
import openerp.netsvc as netsvc
import openerp.addons.decimal_precision as dp
from openerp.report import report_sxw
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

class Parser(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(Parser, self).__init__(cr, uid, name, context)
        self.localcontext.update({
            'get_date': self.get_date,
            
            # production report:
            'get_hour': self.get_hour,
            
            # remain report:
            'get_object_remain': self.get_object_remain,
            'previous_record': self.previous_record,
        })

    def previous_record(self, value=False):
        ''' Save passed value as previouse record
            value: 'init' for setup first False record
                   data for set up this record
                   Nothing for get element
        '''
        if value == 'init':
            self.previous_record_value = False            
            return ''
        if value: # set operation
            self.previous_record_value = value
            return '' 
        else: # get operation
            return self.previous_record_value 

    def get_date(self, ):
        ''' For report time
        '''
        return datetime.now().strftime(DEFAULT_SERVER_DATETIME_FORMAT)

    def get_object_remain(self, ):
        ''' Get as browse obj all record with unsync elements
        '''
        line_ids = self.pool.get('sale.order.line').search(self.cr, self.uid, [
            ('product_uom_maked_qty', '>', 0.0)], order='order_id')
        return self.pool.get('sale.order.line').browse(
            self.cr, self.uid, line_ids)

    def get_hour(self, value):
        ''' Format float with H:MM format
        '''
        try:
            return "%s:%s" % (
                int(value),
                int(60 * (value - int(value))),
                )
        except:
            return "0:00"
        
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
