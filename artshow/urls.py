# Artshow Jockey
# Copyright (C) 2009, 2010 Chris Cogdon
# See file COPYING for licence details

from django.urls import re_path

from . import addbidder
from . import bid_entry
from . import bidderreg
from . import cashier
from . import csvreports
from . import pdfreports
from . import reports
from . import views
from . import voice_auction
from . import workflows

urlpatterns = [
    re_path(r'^$', views.index, name='artshow-home'),
    re_path(r'^entry/$', views.dataentry, name='artshow-dataentry'),
    re_path(r'^entry/bidders/$', addbidder.bulk_add,
            name='artshow-bulk-add-bidders'),
    re_path(r'^entry/bids/$', addbidder.bid_bulk_add,
            name='artshow-bulk-add-bids'),
    re_path(r'^entry/bids/mobile/$', bid_entry.bid_entry,
            name='artshow-mobile-bid-entry'),
    re_path(r'^entry/bids/(?P<artist_id>\d+)/(?P<piece_id>\d+)/$',
            bid_entry.bids),
    re_path(r'^entry/auction_bids/(?P<adult>[yn])/$',
            voice_auction.auction_bids),
    re_path(r'^entry/order_auction/(?P<adult>[yn])/$',
            voice_auction.order_auction,
            name='artshow-voice-auction-order'),
    # re_path(r'^entry/bids/location/(?P<location>[^/]+)/$', bidentry.add_bids),
    re_path(r'^reports/$', reports.index, name='artshow-reports'),
    re_path(r'^artist/(?P<artist_id>\d+)/mailinglabel/$',
            views.artist_mailing_label),
    re_path(r'^artist/(?P<artist_id>\d+)/piecereport/$',
            reports.artist_piece_report),
    re_path(r'^reports/artists/$', reports.artists,
            name='artshow-report-artists'),
    re_path(r'^reports/winning-bidders/$', reports.winning_bidders,
            name='artshow-report-winning-bidders'),
    re_path(r'^reports/unsold-pieces/$', reports.unsold_pieces,
            name='artshow-report-unsold-pieces'),
    re_path(r'^reports/artist-panel-report/$', reports.artist_panel_report,
            name='artshow-report-artist-to-panel'),
    re_path(r'^reports/panel-artist-report/$', reports.panel_artist_report,
            name='artshow-report-panel-to-artist'),
    re_path(r'^reports/artist-payment-report/$', reports.artist_payment_report,
            name='artshow-report-artist-payment'),
    re_path(r'^reports/show-summary/$', reports.show_summary,
            name='artshow-summary'),
    re_path(r'^reports/voice-auction/$', reports.voice_auction,
            name='artshow-report-voice-auction'),
    re_path(r'^reports/sales-percentiles/$', reports.sales_percentiles,
            name='artshow-report-percentiles'),
    re_path(r'^reports/allocations-waiting/$', reports.allocations_waiting,
            name='artshow-report-allocations-waiting'),
    re_path(r'^cashier/$', cashier.cashier, name='artshow-cashier'),
    re_path(r'^cashier/bidder/(?P<bidder_id>\d+)/$', cashier.cashier_bidder,
            name='artshow-cashier-bidder'),
    re_path(r'^cashier/bidder/(?P<bidder_id>\d+)/invoices/$',
            cashier.cashier_bidder_invoices,
            name='artshow-cashier-bidder-invoices'),
    re_path(r'^cashier/invoice/(?P<invoice_id>\d+)/$', cashier.cashier_invoice,
            name='artshow-cashier-invoice'),
    re_path(r'^cashier/invoice/(?P<invoice_id>\d+)/print/$',
            cashier.cashier_print_invoice, name='artshow-print-invoice'),
    re_path(r'^cashier/invoice/(?P<invoice_id>\d+)/pdf/$',
            pdfreports.pdf_invoice),
    re_path(r'^cashier/invoice/(?P<invoice_id>\d+)/picklist/$',
            pdfreports.pdf_picklist),
    re_path(r'^reports/winning-bidders-pdf/$', pdfreports.winning_bidders,
            name='artshow-winning-bidders-pdf'),
    re_path(r'^reports/bid-entry-by-location-pdf/$',
            pdfreports.bid_entry_by_location),
    re_path(r'^reports/artists-csv/$', csvreports.artists,
            name='artshow-artists-csv'),
    re_path(r'^reports/pieces-csv/$', csvreports.pieces,
            name='artshow-pieces-csv'),
    re_path(r'^reports/bidders-csv/$', csvreports.bidders,
            name='artshow-bidders-csv'),
    re_path(r'^reports/payments-csv/$', csvreports.payments,
            name='artshow-payments-csv'),
    re_path(r'^reports/cheques-csv/$', csvreports.cheques,
            name='artshow-cheques-csv'),
    re_path(r'^access/$', views.artist_self_access,
            name='artshow-artist-access'),
    re_path(r'^bidderreg/$', bidderreg.main,
            name='artshow-bidderreg-wizard'),
    re_path(r'^bidderreg/done/$', bidderreg.final,
            name='artshow-bidderreg-final'),
    re_path(r'^bidder/(?P<pk>\d+)/agreement/$', bidderreg.bidder_agreement,
            name='artshow-bidder-agreement'),
    re_path(r'^bidder/$', views.bidder_results),
    re_path(r'^workflows/$', workflows.index, name='artshow-workflows'),
    re_path(r'^workflows/printing/$', workflows.printing,
            name='artshow-workflow-printing'),
    re_path(r'^workflows/artist_checkin/$', workflows.find_artist_checkin,
            name='artshow-workflow-artist-checkin-lookup'),
    re_path(r'^workflows/artist_checkin/(?P<artistid>\d+)/$',
            workflows.artist_checkin, name='artshow-workflow-artist-checkin'),
    re_path(r'^workflows/artist_checkin/(?P<artistid>\d+)/control_form$',
            workflows.artist_print_checkin_control_form,
            name='artshow-workflow-artist-checkin-control-form'),
    re_path(r'^workflows/artist_checkin/(?P<artistid>\d+)/bid_sheets$',
            workflows.artist_print_bid_sheets,
            name='artshow-workflow-artist-bid-sheets'),
    re_path(r'^workflows/artist_checkin/(?P<artistid>\d+)/piece_stickers$',
            workflows.artist_print_piece_stickers,
            name='artshow-workflow-artist-piece-stickers'),
    re_path(r'^workflows/bidder/$', addbidder.find_bidder,
            name='artshow-workflow-bidder-lookup'),
    re_path(r'^workflows/bidder/(?P<pk>\d+)/$', addbidder.bidder_detail,
            name='artshow-workflow-bidder'),
    re_path(r'^workflows/bidder/(?P<pk>\d+)/auto_id$', addbidder.assign_bidder_id,
            name='artshow-workflow-bidder-auto-id'),
    re_path(r'^workflows/create_locations/$', workflows.create_locations,
            name='artshow-workflow-create-locations'),
    re_path(r'^workflows/create_ids/$', workflows.create_bidder_ids,
            name='artshow-workflow-create-bidder-ids'),
    re_path(r'^workflows/close/$', workflows.close_show,
            name='artshow-workflow-close-show'),
    re_path(r'^workflows/printing/cheques/$', workflows.print_cheques,
            name='artshow-workflow-print-cheques'),
    re_path(r'^workflows/printing/cheques/print/$',
            workflows.print_cheques_print,
            name='artshow-workflow-print-cheques-print'),
    re_path(r'^workflows/artist_checkout/$', workflows.find_artist_checkout,
            name='artshow-workflow-artist-checkout-lookup'),
    re_path(r'^workflows/artist_checkout/(?P<artistid>\d+)/$',
            workflows.artist_checkout, name='artshow-workflow-artist-checkout'),
    re_path(r'^workflows/artist_checkout/(?P<artistid>\d+)/control_form$',
            workflows.artist_print_checkout_control_form,
            name='artshow-workflow-artist-checkout-control-form'),
]
