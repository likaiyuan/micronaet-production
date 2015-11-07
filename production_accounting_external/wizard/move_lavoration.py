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

class MrpMoveLavoration(orm.TransientModel):
    ''' Move from one lavoration to end in another date (and recalculate 
        parameters)
    '''
    
    _name = "mrp.production.move.lavoration.wizard"

    # --------------
    # Wizard button:
    # --------------
    def move_lavoration_item(self, cr, uid, ids, context=None):
        ''' Assign production to selected order line
        '''
        if context is None: 
            context = {}        
        active_id = context.get('active_id', False)    

        # Pool used:        
        mrp_pool = self.pool.get('mrp.production')
        wc_pool = self.pool.get('mrp.production.workcenter.line')

        # Read wizard parameters:
        wiz_proxy = self.browse(cr, uid, ids, context=context)[0]        

        # Get all lavorations to move:
        lavoration_ids = wc_pool.search(cr, uid, [
            ('production_id', '=', 
                wiz_proxy.scheduled_lavorarion_id.production_id.id),
            ('date_planned', '>=', 
                wiz_proxy.scheduled_lavorarion_id.date_planned),
            ], context=context)
        
        if not lavoration_ids: # maybe deleted or moved before confirmation
            return True
            
        move_context = context.copy()
        move_context.update({
            'move_lavoration_ids': lavoration_ids,
            'move_date': wiz_proxy.new_date,
            'move_workhour_id': wiz_proxy.workhour_id.id,
            'move_workcenter_id': wiz_proxy.wokrcenter_id.id,
            'move_workers': wiz_proxy.workers,
            'move_bom_id': wiz_proxy.bom_id.id,
            })
        
        mrp_pool.schedule_lavoration(cr, uid, [wiz_proxy.production_id.id], 
            context=move_context)

        return {'type':'ir.actions.act_window_close'}

    # ------------------
    # Defaults function:
    # ------------------
    def _get_info_in_plan(self, cr, uid, field, context=None):
        ''' Read workers in lavoration plan (first for now)
        '''
        if context is None: 
            context = {}
        try:    
            active_id = context.get('active_id', False)    
            wc_pool = self.pool.get('mrp.production.workcenter.line')
            wc_proxy = wc_pool.browse(cr, uid, active_id, context=context)
            
            # Planner:
            if field == 'workers':
                return wc_proxy.production_id.lavoration_ids[0].workers
            elif field == 'workcenter_id':
                return wc_proxy.production_id.lavoration_ids[0].line_id.id
            
            # Lavoration    
            elif field == 'new_date':
                return wc_proxy.date_planned
            
            # MRP:    
            elif field == 'bom_id':
                return wc_proxy.production_id.bom_id.id
            elif field == 'workhour_id':
                return wc_proxy.production_id.workhour_id.id
                
        except:
            pass  # No error
        return False    

    _columns = {
        # Split info_
        'new_date': fields.datetime('New date', required=True),
        'scheduled_lavoration_id': fields.many2one(
            'mrp.production.workcenter.line',
            'Current start point'),
        'note': fields.text(
            'Note', 
            help='Add extra info to specify why lavoration are moved'),
        
        # Parameters:
        # TODO parametrize all for create new elements instead of move:
        'workhour_id': fields.many2one('hr.workhour', 'Work hour', 
            readonly=True),
        'bom_id': fields.many2one('mrp.bom', 'BOM', 
            readonly=True),
        'workcenter_id': fields.many2one('mrp.workcenter', 'Workcenter',
            readonly=True),
        'workers': fields.integer('Workers', 
            readonly=True),
        }

    _defaults = {
        # MRP     
        'bom_id': lambda s, cr, uid, ctx: s._get_info_in_plan(
            cr, uid, 'bom_id', ctx),
        'workhour_id': lambda s, cr, uid, ctx: s._get_info_in_plan(
            cr, uid, 'workhour_id', ctx),

        # Lavoration:
        'new_date': lambda s, cr, uid, ctx: s._get_info_in_plan(
            cr, uid, 'new_date', ctx),

        # Planner:
        'workers': lambda s, cr, uid, ctx: s._get_info_in_plan(
            cr, uid, 'workers', ctx),
        'workcenter_id': lambda s, cr, uid, ctx: s._get_info_in_plan(
            cr, uid, 'workcenter_id', ctx),
        }
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
