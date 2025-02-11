from django import forms
from django.contrib import messages
from django.contrib.auth.decorators import permission_required
from django.db.models import Q
from django.forms.models import inlineformset_factory, modelformset_factory
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from .conf import settings
from .mod11codes import make_check
from .models import Artist, BidderId, ChequePayment, Location, Piece, Space


@permission_required('artshow.is_artshow_staff')
def index(request):
    return render(request, 'artshow/workflows_index.html')


@permission_required('artshow.is_artshow_staff')
def printing(request):
    bid_sheets_query = Piece.objects.filter(status__in=(Piece.StatusNotInShow, Piece.StatusNotInShowLocked),
                                            bid_sheet_printing=Piece.PrintingNotPrinted)
    control_forms_query = Piece.objects.filter(status__in=(Piece.StatusNotInShow, Piece.StatusNotInShowLocked),
                                               control_form_printing=Piece.PrintingNotPrinted)
    bid_sheets_to_print_query = Piece.objects.filter(bid_sheet_printing=Piece.PrintingToBePrinted).order_by('artist__artistid', 'pieceid')
    control_forms_to_print_query = Piece.objects.filter(control_form_printing=Piece.PrintingToBePrinted).order_by('artist__artistid', 'pieceid')

    if request.method == "POST":
        if request.POST.get("lock_pieces"):
            bid_sheets_marked = bid_sheets_query.update(
                status=Piece.StatusNotInShowLocked,
                bid_sheet_printing=Piece.PrintingToBePrinted)
            control_forms_marked = control_forms_query.update(
                status=Piece.StatusNotInShowLocked,
                control_form_printing=Piece.PrintingToBePrinted)
            messages.info(request, "%d pieces have been marked for bid sheet printing, %d for control form printing" % (
                bid_sheets_marked, control_forms_marked))
            return redirect('.')
        elif request.POST.get("print_bid_sheets"):
            from . import bidsheets
            response = HttpResponse(content_type="application/pdf")
            bidsheets.generate_bidsheets(output=response, pieces=bid_sheets_to_print_query)
            messages.info(request, "Bid sheets printed.")
            return response

        elif request.POST.get("print_control_forms"):
            from . import bidsheets
            response = HttpResponse(content_type="application/pdf")
            bidsheets.generate_control_forms_for_pieces(output=response, pieces=control_forms_to_print_query)
            messages.info(request, "Control forms printed.")
            return response

        elif request.POST.get("bid_sheets_done"):
            pieces_marked = bid_sheets_to_print_query.update(bid_sheet_printing=Piece.PrintingPrinted)
            messages.info(request, "%d pieces marked as bid sheet printed" % pieces_marked)
            return redirect('.')

        elif request.POST.get("control_forms_done"):
            pieces_marked = control_forms_to_print_query.update(control_form_printing=Piece.PrintingPrinted)
            messages.info(request, "%d pieces marked as control form printed" % pieces_marked)
            return redirect('.')

    context = {
        'num_pieces_bid_sheet_unprinted': bid_sheets_query.count(),
        'num_pieces_control_form_unprinted': control_forms_query.count(),
        'num_bid_sheets_to_be_printed': bid_sheets_to_print_query.count(),
        'num_control_forms_to_be_printed': control_forms_to_print_query.count(),
        'num_bid_sheets_printed': Piece.objects.filter(bid_sheet_printing=Piece.PrintingPrinted).count(),
        'num_control_forms_printed': Piece.objects.filter(control_form_printing=Piece.PrintingPrinted).count(),
    }

    return render(request, 'artshow/workflows_printing.html', context)


class ArtistSearchForm(forms.Form):
    text = forms.CharField(label="Search Text")


@permission_required('artshow.is_artshow_staff')
def find_artist_checkin(request):
    search_executed = False
    if request.method == "POST":
        form = ArtistSearchForm(request.POST)
        if form.is_valid():
            text = form.cleaned_data['text']
            query = (Q(person__name__icontains=text)
                     | Q(publicname__icontains=text))
            try:
                artistid = int(text)
                query = query | Q(artistid=artistid)
            except ValueError:
                pass
            artists = Artist.objects.filter(query)
            search_executed = True
        else:
            artists = []
    else:
        form = ArtistSearchForm()
        artists = []

    c = {"form": form, "artists": artists, "search_executed": search_executed}
    return render(request, 'artshow/workflows_artist_checkin_lookup.html', c)


class PieceCheckinForm(forms.ModelForm):
    location = forms.ChoiceField(choices=[], required=False)
    print_item = forms.BooleanField(label='Print', initial=False,
                                    required=False)

    class Meta:
        model = Piece
        fields = (
            'print_item', 'pieceid', 'name', 'media', 'adult',
            'reproduction_rights_included', 'not_for_sale', 'min_bid',
            'buy_now', 'location',
        )
        widgets = {
            'pieceid': forms.TextInput(attrs={'size': 4}),
            'name': forms.TextInput(attrs={'size': 40}),
            'media': forms.TextInput(attrs={'size': 40}),
            'min_bid': forms.TextInput(attrs={'size': 5}),
            'buy_now': forms.TextInput(attrs={'size': 5}),
        }

    def __init__(self, **kwargs):
        try:
            artist_locations = kwargs.pop('artist_locations')
        except KeyError:
            artist_locations = []
        super().__init__(**kwargs)
        self.fields['location'].choices = [('', '---')]
        self.fields['location'].choices.extend([(l, l) for l in artist_locations])
        if self.instance.id is not None:
            self.initial['print_item'] = True
            self.initial['location'] = self.instance.location


PieceCheckinFormSet = inlineformset_factory(Artist, Piece,
                                            form=PieceCheckinForm,
                                            extra=3, can_delete=False)


@permission_required('artshow.is_artshow_staff')
def artist_checkin(request, artistid):
    artist = get_object_or_404(Artist, artistid=artistid)
    queryset = artist.piece_set \
        .filter(status__in=(Piece.StatusNotInShow,
                            Piece.StatusInShow)) \
        .order_by('pieceid')
    if request.method == 'POST':
        formset = PieceCheckinFormSet(request.POST, queryset=queryset,
                                      instance=artist,
                                      form_kwargs={'artist_locations': artist.assigned_locations()})
        if formset.is_valid():
            formset.save()
            # Create a fresh formset for further edits.
            formset = PieceCheckinFormSet(queryset=queryset, instance=artist,
                                          form_kwargs={'artist_locations': artist.assigned_locations()})
    else:
        formset = PieceCheckinFormSet(queryset=queryset, instance=artist,
                                      form_kwargs={'artist_locations': artist.assigned_locations()})

    json_data = {
        'artistId': artist.artistid,
        'artistName': artist.artistname(),
    }

    c = {
        'artist': artist,
        'formset': formset,
        'json_data': json_data,
    }
    return render(request, 'artshow/workflows_artist_checkin.html', c)


@permission_required('artshow.is_artshow_staff')
@require_POST
def artist_print_checkin_control_form(request, artistid):
    artist = get_object_or_404(Artist, artistid=artistid)
    queryset = artist.piece_set.order_by('pieceid')
    formset = PieceCheckinFormSet(request.POST, queryset=queryset,
                                  instance=artist,
                                  form_kwargs={'artist_locations': artist.assigned_locations()})
    if not formset.is_valid():
        c = {'artist': artist, 'formset': formset}
        return render(request, 'artshow/workflows_artist_checkin.html', c)
    formset.save()

    c = {
        'artists': [artist],
        'check_in': True,
        'print': True,
        'redirect': reverse('artshow-workflow-artist-checkin',
                            kwargs={'artistid': artist.artistid}),
    }
    return render(request, 'artshow/control_form.html', c)


@permission_required('artshow.is_artshow_staff')
@require_POST
def artist_print_bid_sheets(request, artistid):
    artist = get_object_or_404(Artist, artistid=artistid)
    queryset = artist.piece_set.order_by('pieceid')
    formset = PieceCheckinFormSet(request.POST, queryset=queryset,
                                  instance=artist,
                                  form_kwargs={'artist_locations': artist.assigned_locations()})
    if not formset.is_valid():
        c = {'artist': artist, 'formset': formset}
        return render(request, 'artshow/workflows_artist_checkin.html', c)
    formset.save()

    pieces = []
    for form in formset:
        if 'print_item' in form.cleaned_data \
                and form.cleaned_data['print_item']:
            pieces.append(form.instance)

    c = {
        'pieces': pieces,
        'print': True,
        'redirect': reverse('artshow-workflow-artist-checkin',
                            kwargs={'artistid': artist.artistid}),
    }
    return render(request, 'artshow/bid_sheets.html', c)


@permission_required('artshow.is_artshow_staff')
@require_POST
def artist_print_piece_stickers(request, artistid):
    artist = get_object_or_404(Artist, artistid=artistid)
    queryset = artist.piece_set.order_by('pieceid')
    formset = PieceCheckinFormSet(request.POST, queryset=queryset,
                                  instance=artist,
                                  form_kwargs={'artist_locations': artist.assigned_locations()})
    if not formset.is_valid():
        c = {'artist': artist, 'formset': formset}
        return render(request, 'artshow/workflows_artist_checkin.html', c)
    formset.save()

    pieces = []
    for form in formset:
        if 'print_item' in form.cleaned_data \
                and form.cleaned_data['print_item']:
            pieces.append(form.instance)

    c = {
        'pieces': pieces,
        'print': True,
        'redirect': reverse('artshow-workflow-artist-checkin',
                            kwargs={'artistid': artist.artistid}),
    }
    return render(request, 'artshow/piece_stickers.html', c)


@permission_required('artshow.is_artshow_staff')
def find_artist_checkout(request):
    search_executed = False
    if request.method == "POST":
        form = ArtistSearchForm(request.POST)
        if form.is_valid():
            text = form.cleaned_data['text']
            query = (Q(person__name__icontains=text)
                     | Q(publicname__icontains=text))
            try:
                artistid = int(text)
                query = query | Q(artistid=artistid)
            except ValueError:
                pass
            artists = Artist.objects.filter(query)
            search_executed = True
        else:
            artists = []
    else:
        form = ArtistSearchForm()
        artists = []

    c = {"form": form, "artists": artists, "search_executed": search_executed}
    return render(request, 'artshow/workflows_artist_checkout_lookup.html', c)


class PieceCheckoutForm(forms.ModelForm):
    returned = forms.BooleanField(label='Returned',
                                  initial=False,
                                  required=False)

    class Meta:
        model = Piece
        fields = ()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if self.instance.status is Piece.StatusReturned:
            self.fields['returned'].initial = True


PieceCheckoutFormSet = modelformset_factory(Piece, form=PieceCheckoutForm,
                                            extra=0, can_delete=False)


@permission_required('artshow.is_artshow_staff')
def artist_checkout(request, artistid):
    artist = get_object_or_404(Artist, artistid=artistid)
    queryset = artist.piece_set.filter(Q(status=Piece.StatusInShow)
                                       | Q(status=Piece.StatusReturned)) \
        .exclude(voice_auction=True).order_by('pieceid')
    if request.method == 'POST':
        formset = PieceCheckoutFormSet(request.POST, queryset=queryset)
        if formset.is_valid():
            for form in formset:
                if form.cleaned_data['returned']:
                    form.instance.status = Piece.StatusReturned
                else:
                    form.instance.status = Piece.StatusInShow
                form.instance.save()
    else:
        formset = PieceCheckoutFormSet(queryset=queryset)

    sold_pieces = artist.piece_set.filter(
        Q(status=Piece.StatusWon)
        | Q(status=Piece.StatusSold)).order_by('pieceid')
    voice_auction = artist.piece_set.filter(status=Piece.StatusInShow,
                                            voice_auction=True) \
        .order_by('pieceid')
    cheques = ChequePayment.objects.filter(artist=artist)

    c = {
        'artist': artist,
        'formset': formset,
        'sold_pieces': sold_pieces,
        'voice_auction': voice_auction,
        'cheques': cheques,
    }
    return render(request, 'artshow/workflows_artist_checkout.html', c)


@permission_required('artshow.is_artshow_staff')
def artist_print_checkout_control_form(request, artistid):
    artist = get_object_or_404(Artist, artistid=artistid)
    c = {
        'artists': [artist],
        'check_out': True,
        'print': True,
        'redirect': reverse('artshow-workflow-artist-checkout',
                            kwargs={'artistid': artist.artistid}),
    }
    return render(request, 'artshow/control_form.html', c)


class CreateLocationsForm(forms.Form):
    type = forms.ModelChoiceField(label='Space', queryset=Space.objects)
    prefix = forms.CharField(label='Prefix', max_length=1)
    start_value = forms.IntegerField(label='Starting value', min_value=1)
    count = forms.IntegerField(label='Count', min_value=1)


@permission_required('artshow.is_artshow_staff')
def create_locations(request):
    if request.method == 'POST':
        form = CreateLocationsForm(request.POST)
        if form.is_valid():
            type = form.cleaned_data['type']
            prefix = form.cleaned_data['prefix']
            start = form.cleaned_data['start_value']
            count = form.cleaned_data['count']
            locations = [Location(type=type, name=prefix + str(index))
                         for index in range(start, start + count)]
            Location.objects.bulk_create(locations)
    else:
        form = CreateLocationsForm()

    c = {
        'form': form,
        'locations': Location.objects.sorted(),
    }
    return render(request, 'artshow/workflows_create_locations.html', c)


class CreateBidderIdsForm(forms.Form):
    num_ids = forms.IntegerField(label="New IDs")


@permission_required('artshow.is_artshow_staff')
def create_bidder_ids(request):
    total_ids = BidderId.objects.count()
    try:
        last_id = BidderId.objects.latest('id').id
    except BidderId.DoesNotExist:
        last_id = None

    if request.method == 'POST':
        form = CreateBidderIdsForm(request.POST)
        if form.is_valid():
            desired_ids = total_ids + form.cleaned_data['num_ids']
            if last_id is None:
                value = 1
            else:
                value = int(last_id[:-1]) + 1

            new_ids = []
            while total_ids < desired_ids:
                code = '%0*d' % (3, value)
                value += 1
                check = make_check(code, offset=settings.ARTSHOW_BIDDERID_MOD11_OFFSET)
                if check == 'X':
                    continue

                last_id = code + check
                new_ids.append(BidderId(id=last_id))
                total_ids += 1
            BidderId.objects.bulk_create(new_ids)
    else:
        form = CreateBidderIdsForm()

    try:
        first_id = BidderId.objects.earliest('id').id
    except BidderId.DoesNotExist:
        first_id = None

    try:
        first_used_id = BidderId.objects.filter(bidder__isnull=False).earliest('id').id
    except BidderId.DoesNotExist:
        first_used_id = None

    try:
        last_used_id = BidderId.objects.filter(bidder__isnull=False).latest('id').id
    except BidderId.DoesNotExist:
        last_used_id = None

    c = {
        'total_ids': total_ids,
        'first_id': first_id,
        'first_used_id': first_used_id,
        'last_id': last_id,
        'last_used_id': last_used_id,
        'form': form,
    }
    return render(request, 'artshow/workflows_create_bidder_ids.html', c)


@permission_required('artshow.is_artshow_staff')
def close_show(request):
    if request.method == 'POST':
        # Apply won/voice auction status.
        for piece in Piece.objects.filter(status=Piece.StatusInShow):
            piece.apply_won_status()

    artists_total = 0
    voice_auction_remaining = 0
    artists_processed = 0
    artists_remaining = 0
    for artist in Artist.objects.all():
        artists_total += 1

        # Skip artists who still have pieces in voice auction.
        if artist.piece_set.filter(status=Piece.StatusInShow,
                                   voice_auction=True).exists():
            voice_auction_remaining += 1
            continue

        if artist.payment_set.filter(
                payment_type_id__in=(settings.ARTSHOW_SPACE_FEE_PK,
                                     settings.ARTSHOW_COMMISSION_PK,
                                     settings.ARTSHOW_SALES_PK)).exists():
            artists_processed += 1
            continue

        if request.method == 'POST':
            artist_queryset = Artist.objects.filter(pk=artist.pk)
            Artist.apply_space_fees(artist_queryset)
            Artist.apply_winnings_and_commission(artist_queryset)
            Artist.create_cheques(artist_queryset)
            artists_processed += 1
        else:
            artists_remaining += 1

    c = {
        'pieces_not_in_show':
            Piece.objects.filter(status=Piece.StatusNotInShow).count(),
        'pieces_in_show':
            Piece.objects.filter(status=Piece.StatusInShow,
                                 voice_auction=False).count(),
        'pieces_awaiting_voice_auction':
            Piece.objects.filter(status=Piece.StatusInShow,
                                 voice_auction=True).count(),
        'pieces_won':
            Piece.objects.filter(status=Piece.StatusWon).count(),
        'pieces_sold':
            Piece.objects.filter(status=Piece.StatusSold).count(),
        'pieces_returned':
            Piece.objects.filter(status=Piece.StatusReturned).count(),
        'artists_total': artists_total,
        'voice_auction_remaining': voice_auction_remaining,
        'artists_processed': artists_processed,
        'artists_remaining': artists_remaining,
    }
    return render(request, 'artshow/workflows_close_show.html', c)


ChequeFormSet = modelformset_factory(ChequePayment, fields=('number',),
                                     extra=0, can_delete=False)


@permission_required('artshow.is_artshow_staff')
def print_cheques(request):
    queryset = ChequePayment.objects.filter(number='')
    if request.method == 'POST':
        formset = ChequeFormSet(request.POST, queryset=queryset)
        if formset.is_valid():
            formset.save()
            formset = ChequeFormSet(queryset=queryset)
    else:
        formset = ChequeFormSet(queryset=queryset)

    printed_cheques = ChequePayment.objects.exclude(number='')

    c = {'formset': formset, 'printed_cheques': printed_cheques}
    return render(request, 'artshow/workflows_print_cheques.html', c)


@permission_required('artshow.is_artshow_staff')
@require_POST
def print_cheques_print(request):
    cheques = ChequePayment.objects.filter(number='')

    c = {
        'cheques': cheques,
        'print': True,
        'redirect': reverse('artshow-workflow-print-cheques'),
    }
    return render(request, 'artshow/cheque.html', c)
