from django.shortcuts import redirect, render
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.http import JsonResponse, HttpResponse, response, FileResponse
from django.template.loader import get_template,render_to_string
from django.utils.html import strip_tags
from django.contrib.auth.decorators import permission_required, login_required
import datetime
from datetime import *
from django.conf import settings
from .models import *
from django.core.mail import send_mail,EmailMultiAlternatives
import json
import uuid
from PIL import Image
from django.views.decorators.csrf import csrf_protect
from django.core.files.storage import FileSystemStorage
from django.db.models.query_utils import Q
from django.db.models import Count, F, Value, Avg, Max, Sum, Min, Subquery, OuterRef

#pdf
from django.template.loader import get_template,render_to_string
import os
from io import BytesIO
from xhtml2pdf import pisa
#from weasyprint import HTML
#import tempfile
from num2words import num2words
import pandas as pd


# Create your views here.

def gimmo(request):
    mois_apres_pay = 2
    start_date = datetime.today()
    date_1 = pd.to_datetime(start_date)
    end_date = date_1+pd.DateOffset(months=(mois_apres_pay))

    etat = 0
    diff_in_hours = 1
    countSoftkey = Softkeyactive.objects.all().count()
    
    #ETABLISSEMENT
    if Etablissement.objects.all().count() == 0:
        count_etablissement = Etablissement.objects.all().count()
        idpub_ref = uuid.uuid4()
        idpub_ref = str(idpub_ref).replace("-","")
        publicid = idpub_ref + str(count_etablissement)

        Etablissement.objects.create(
            idpub = publicid,
            raisonsocial = '',
            formejuridique = '',
            comptecontribuable = '',
            registrecommerce = '',
            secteur = '',
            telfixe = '',
            tel = '',
            siege = '',
            adresse = '',
            email = '',
            devise = 'XOF',
            visitemtt = 0,
            honorairemtt = 0,
            droitmtt = 0,
            timbremtt = 0,
            fraisdossiermtt = 0,
            assurancemtt = 0,
            tva = 0,
            margepay = 2,
            activepro = True,
            activeloc = True,
            emailsend = True,
            smssend = False,
            ouverture = '2021-12-14',
            etat = 1,
            logo = '',
            tampon = '',
            creation = datetime.now()
        ).save()

    if request.method == 'POST':
        username = request.POST.get('username', False)
        password = request.POST.get('password', False)
        #remenber = request.POST.get('rememberme', False)
        
        user = authenticate(request, username=username, password=password)
        if user:
            if user is not None:
                login(request, user)
                Log.objects.create(
                    actiondate = datetime.now(),
                    actiontext = 1,
                    user = User.objects.get(username=username)
                ).save()
                return redirect('accueil')
        else:
            etat = 1
    
    if countSoftkey == 0:
        start_date = datetime.today()
        date_1 = pd.to_datetime(start_date)
        end_date = date_1+pd.DateOffset(days=20)
        softk = uuid.uuid4()
        Softkeyactive.objects.create(
            keyword = softk,
            datesoft = end_date
        )
        diff_in_hours = 1
    else:
        end_date_soft = Softkeyactive.objects.last().datesoft
        #print(end_date_soft) 
        date_1 = str(datetime.now())
        date_2 = str(end_date_soft)
        n_date_2 = date_2[:19]
        n_date_1 = date_1[:19]
        
        date_format_str = '%Y-%m-%d %H:%M:%S'
        start = datetime.strptime(n_date_1, date_format_str)
        end =   datetime.strptime(n_date_2, date_format_str)
        # Get interval between two timstamps as timedelta object
        diff = end - start
        diff_in_hours = (diff.total_seconds() / 3600)
        diff_in_hours = diff_in_hours /24
        
    
    if diff_in_hours < 0.1:
        all_user = User.objects.filter(is_staff=0)
        for all_u in all_user:
            User.objects.filter(id=all_u.id).update(
                is_active = 0
            )
    else:
        all_user = User.objects.filter(is_staff=0)
        for all_u in all_user:
            User.objects.filter(id=all_u.id).update(
                is_active = 1
            )

    content = {
        'etat':etat,
        'diff_in_hours':round(diff_in_hours,1)
    }
    return render(request,'gimmo/index.html',content)

def senEmail(sujet,contrat,message,ref_facture):
    #print(contrat.locative.typelocative)
    content = {
        'un_contrat':contrat,
        'message':message,
        'sujet':'Loyer '+str(sujet),
        'une_facture':Facture.objects.get(reffacture=ref_facture),
        'un_etablissement': Etablissement.objects.get(id=Etablissement.objects.last().id)
      }
      
    subject, from_email, to = sujet, settings.DEFAULT_FROM_EMAIL, contrat.locataire.user.email
    html_content = render_to_string('gimmo/pages/parametre/email-facture.html', content) # render with dynamic value
    text_content = strip_tags(html_content) # Strip the html tag. So people can see the pure text at least.
    #create the email, and attach the HTML version as well.
    msg = EmailMultiAlternatives(subject, text_content, from_email, [to])
    msg.attach_alternative(html_content, "text/html")
    msg.send()
    print('super nice')

def deconnexion(request):
    Log.objects.create(
        actiondate = datetime.now(),
        actiontext = "Fermeture",
        user = request.user
    ).save()
    logout(request)

    return redirect('/')

#####ACCUEIL
@login_required(login_url='/')
def accueil(request):
    etat = 0
    diff_in_hours = 1
    countSoftkey = Softkeyactive.objects.all().count()
    mois_encours = date.today().month
    annee_encours = date.today().year

    if Locataire.objects.filter(user=request.user).exists():
        facture_gene = Facture.objects.filter(creation__month=mois_encours,creation__year=annee_encours,locataire_id=request.user.locataire.id).aggregate(tot=Sum('finaltotal'))
        facture_gene = facture_gene['tot']
        if facture_gene == None:
            facture_gene = 0
        else:
            facture_gene = facture_gene
        
        facture_paye = Facture.objects.filter(creation__month=mois_encours,creation__year=annee_encours,locataire_id=request.user.locataire.id,etat=1).aggregate(tot=Sum('finaltotal'))
        facture_paye = facture_paye['tot']
        if facture_paye == None:
            facture_paye = 0
        else:
            facture_paye = facture_paye
        
        facture_imp = Facture.objects.filter(Q(etat__gte=2)|Q(etat=0),creation__month=mois_encours,creation__year=annee_encours,locataire_id=request.user.locataire.id).aggregate(tot=Sum('finaltotal'))
        facture_imp = facture_imp['tot']
        if facture_imp == None:
            facture_imp = 0
        else:
            facture_imp = facture_imp
        
    elif Proprietaire.objects.filter(user=request.user).exists():
        #contrat__proprietaire__id=Proprietaire.objects.get(user=request.user).id
        facture_gene = 0
        
        facture_paye = 0
        
        facture_imp = 0

        facture_gene = Facture.objects.filter(creation__month=mois_encours,creation__year=annee_encours,contrat__proprietaire__id=Proprietaire.objects.get(user=request.user).id).aggregate(tot=Sum('finaltotal'))
        facture_gene = facture_gene['tot']
        if facture_gene == None:
            facture_gene = 0
        else:
            facture_gene = facture_gene
        
        facture_paye = Facture.objects.filter(creation__month=mois_encours,creation__year=annee_encours,contrat__proprietaire__id=Proprietaire.objects.get(user=request.user).id,etat=1).aggregate(tot=Sum('finaltotal'))
        facture_paye = facture_paye['tot']
        if facture_paye == None:
            facture_paye = 0
        else:
            facture_paye = facture_paye
        
        facture_imp = Facture.objects.filter(Q(etat__gte=2)|Q(etat=0),creation__month=mois_encours,creation__year=annee_encours,contrat__proprietaire__id=Proprietaire.objects.get(user=request.user).id).aggregate(tot=Sum('finaltotal'))
        facture_imp = facture_imp['tot']
        if facture_imp == None:
            facture_imp = 0
        else:
            facture_imp = facture_imp
    else:
        facture_gene = Facture.objects.filter(creation__month=mois_encours,creation__year=annee_encours).aggregate(tot=Sum('finaltotal'))
        facture_gene = facture_gene['tot']
        if facture_gene == None:
            facture_gene = 0
        else:
            facture_gene = facture_gene
        
        facture_paye = Facture.objects.filter(creation__month=mois_encours,creation__year=annee_encours,etat=1).aggregate(tot=Sum('finaltotal'))
        facture_paye = facture_paye['tot']
        if facture_paye == None:
            facture_paye = 0
        else:
            facture_paye = facture_paye
        
        facture_imp = Facture.objects.filter(Q(etat__gte=2)|Q(etat=0),creation__month=mois_encours,creation__year=annee_encours).aggregate(tot=Sum('finaltotal'))
        facture_imp = facture_imp['tot']
        if facture_imp == None:
            facture_imp = 0
        else:
            facture_imp = facture_imp


    derniere_facture = Facturedetails.objects.filter(Q(facture__etat=1)|Q(facture__etat=4)).order_by('-creation')[0:7]
    
    
    
    
    depense_mois = Depense.objects.filter(creation__month=mois_encours,creation__year=annee_encours).aggregate(tot=Sum('valeur'))
    depense_mois = depense_mois['tot']
    if depense_mois == None:
        depense_mois = 0
    else:
        depense_mois = depense_mois

    tab_mois = [
        'Janvier',
        'Février',
        'Mars',
        'Avril',
        'Mai',
        'Juin',
        'Juillet',
        'Aout',
        'Septembre',
        'Octobre',
        'Novembre',
        'Décembre'
    ]
    if facture_gene == 0:
        percentage_paye = 0
        percentage_impaye = 0
    else:
        percentage_paye = (facture_paye/facture_gene)*100
        percentage_impaye = (facture_imp/facture_gene)*100

    ################PAIEMENT MOIS
    if Locataire.objects.filter(user=request.user).exists():
        facture_jan = Facture.objects.filter(etat=1,creation__month=1,creation__year=annee_encours,locataire_id=request.user.locataire.id).aggregate(tot=Sum('finaltotal'))
        facture_jan = facture_jan['tot']
        if facture_jan == None:
            facture_jan = 0
        else:
            facture_jan = facture_jan

        facture_fev = Facture.objects.filter(etat=1,creation__month=2,creation__year=annee_encours,locataire_id=request.user.locataire.id).aggregate(tot=Sum('finaltotal'))
        facture_fev = facture_fev['tot']
        if facture_fev == None:
            facture_fev = 0
        else:
            facture_fev = facture_fev

        facture_mars = Facture.objects.filter(etat=1,creation__month=3,creation__year=annee_encours,locataire_id=request.user.locataire.id).aggregate(tot=Sum('finaltotal'))
        facture_mars = facture_mars['tot']
        if facture_mars == None:
            facture_mars = 0
        else:
            facture_mars = facture_mars
        
        facture_avr = Facture.objects.filter(etat=1,creation__month=4,creation__year=annee_encours,locataire_id=request.user.locataire.id).aggregate(tot=Sum('finaltotal'))
        facture_avr = facture_avr['tot']
        if facture_avr == None:
            facture_avr = 0
        else:
            facture_avr = facture_avr
        
        facture_mai = Facture.objects.filter(etat=1,creation__month=5,creation__year=annee_encours,locataire_id=request.user.locataire.id).aggregate(tot=Sum('finaltotal'))
        facture_mai = facture_mai['tot']
        if facture_mai == None:
            facture_mai = 0
        else:
            facture_mai = facture_mai
        
        facture_juin = Facture.objects.filter(etat=1,creation__month=6,creation__year=annee_encours,locataire_id=request.user.locataire.id).aggregate(tot=Sum('finaltotal'))
        facture_juin = facture_juin['tot']
        if facture_juin == None:
            facture_juin = 0
        else:
            facture_juin = facture_juin
        
        facture_juil = Facture.objects.filter(etat=1,creation__month=7,creation__year=annee_encours,locataire_id=request.user.locataire.id).aggregate(tot=Sum('finaltotal'))
        facture_juil = facture_juil['tot']
        if facture_juil == None:
            facture_juil = 0
        else:
            facture_juil = facture_juil
        
        facture_aout = Facture.objects.filter(etat=1,creation__month=8,creation__year=annee_encours,locataire_id=request.user.locataire.id).aggregate(tot=Sum('finaltotal'))
        facture_aout = facture_aout['tot']
        if facture_aout == None:
            facture_aout = 0
        else:
            facture_aout = facture_aout
        
        facture_sept = Facture.objects.filter(etat=1,creation__month=9,creation__year=annee_encours,locataire_id=request.user.locataire.id).aggregate(tot=Sum('finaltotal'))
        facture_sept = facture_sept['tot']
        if facture_sept == None:
            facture_sept = 0
        else:
            facture_sept = facture_sept
        
        facture_oct = Facture.objects.filter(etat=1,creation__month=10,creation__year=annee_encours,locataire_id=request.user.locataire.id).aggregate(tot=Sum('finaltotal'))
        facture_oct = facture_oct['tot']
        if facture_oct == None:
            facture_oct = 0
        else:
            facture_oct = facture_oct
        
        facture_nov = Facture.objects.filter(etat=1,creation__month=11,creation__year=annee_encours,locataire_id=request.user.locataire.id).aggregate(tot=Sum('finaltotal'))
        facture_nov = facture_nov['tot']
        if facture_nov == None:
            facture_nov = 0
        else:
            facture_nov = facture_nov
        
        facture_dec = Facture.objects.filter(etat=1,creation__month=12,creation__year=annee_encours,locataire_id=request.user.locataire.id).aggregate(tot=Sum('finaltotal'))
        facture_dec = facture_dec['tot']
        if facture_dec == None:
            facture_dec = 0
        else:
            facture_dec = facture_dec

    elif Proprietaire.objects.filter(user=request.user).exists():
        facture_jan = Facture.objects.filter(etat=1,creation__month=1,creation__year=annee_encours,contrat__proprietaire__id=Proprietaire.objects.get(user=request.user).id).aggregate(tot=Sum('finaltotal'))
        facture_jan = facture_jan['tot']
        if facture_jan == None:
            facture_jan = 0
        else:
            facture_jan = facture_jan

        facture_fev = Facture.objects.filter(etat=1,creation__month=2,creation__year=annee_encours,contrat__proprietaire__id=Proprietaire.objects.get(user=request.user).id).aggregate(tot=Sum('finaltotal'))
        facture_fev = facture_fev['tot']
        if facture_fev == None:
            facture_fev = 0
        else:
            facture_fev = facture_fev

        facture_mars = Facture.objects.filter(etat=1,creation__month=3,creation__year=annee_encours,contrat__proprietaire__id=Proprietaire.objects.get(user=request.user).id).aggregate(tot=Sum('finaltotal'))
        facture_mars = facture_mars['tot']
        if facture_mars == None:
            facture_mars = 0
        else:
            facture_mars = facture_mars
        
        facture_avr = Facture.objects.filter(etat=1,creation__month=4,creation__year=annee_encours,contrat__proprietaire__id=Proprietaire.objects.get(user=request.user).id).aggregate(tot=Sum('finaltotal'))
        facture_avr = facture_avr['tot']
        if facture_avr == None:
            facture_avr = 0
        else:
            facture_avr = facture_avr
        
        facture_mai = Facture.objects.filter(etat=1,creation__month=5,creation__year=annee_encours,contrat__proprietaire__id=Proprietaire.objects.get(user=request.user).id).aggregate(tot=Sum('finaltotal'))
        facture_mai = facture_mai['tot']
        if facture_mai == None:
            facture_mai = 0
        else:
            facture_mai = facture_mai
        
        facture_juin = Facture.objects.filter(etat=1,creation__month=6,creation__year=annee_encours,contrat__proprietaire__id=Proprietaire.objects.get(user=request.user).id).aggregate(tot=Sum('finaltotal'))
        facture_juin = facture_juin['tot']
        if facture_juin == None:
            facture_juin = 0
        else:
            facture_juin = facture_juin
        
        facture_juil = Facture.objects.filter(etat=1,creation__month=7,creation__year=annee_encours,contrat__proprietaire__id=Proprietaire.objects.get(user=request.user).id).aggregate(tot=Sum('finaltotal'))
        facture_juil = facture_juil['tot']
        if facture_juil == None:
            facture_juil = 0
        else:
            facture_juil = facture_juil
        
        facture_aout = Facture.objects.filter(etat=1,creation__month=8,creation__year=annee_encours,contrat__proprietaire__id=Proprietaire.objects.get(user=request.user).id).aggregate(tot=Sum('finaltotal'))
        facture_aout = facture_aout['tot']
        if facture_aout == None:
            facture_aout = 0
        else:
            facture_aout = facture_aout
        
        facture_sept = Facture.objects.filter(etat=1,creation__month=9,creation__year=annee_encours,contrat__proprietaire__id=Proprietaire.objects.get(user=request.user).id).aggregate(tot=Sum('finaltotal'))
        facture_sept = facture_sept['tot']
        if facture_sept == None:
            facture_sept = 0
        else:
            facture_sept = facture_sept
        
        facture_oct = Facture.objects.filter(etat=1,creation__month=10,creation__year=annee_encours,contrat__proprietaire__id=Proprietaire.objects.get(user=request.user).id).aggregate(tot=Sum('finaltotal'))
        facture_oct = facture_oct['tot']
        if facture_oct == None:
            facture_oct = 0
        else:
            facture_oct = facture_oct
        
        facture_nov = Facture.objects.filter(etat=1,creation__month=11,creation__year=annee_encours,contrat__proprietaire__id=Proprietaire.objects.get(user=request.user).id).aggregate(tot=Sum('finaltotal'))
        facture_nov = facture_nov['tot']
        if facture_nov == None:
            facture_nov = 0
        else:
            facture_nov = facture_nov
        
        facture_dec = Facture.objects.filter(etat=1,creation__month=12,creation__year=annee_encours,contrat__proprietaire__id=Proprietaire.objects.get(user=request.user).id).aggregate(tot=Sum('finaltotal'))
        facture_dec = facture_dec['tot']
        if facture_dec == None:
            facture_dec = 0
        else:
            facture_dec = facture_dec
    
    else:
        facture_jan = Facture.objects.filter(etat=1,creation__month=1,creation__year=annee_encours).aggregate(tot=Sum('finaltotal'))
        facture_jan = facture_jan['tot']
        if facture_jan == None:
            facture_jan = 0
        else:
            facture_jan = facture_jan

        facture_fev = Facture.objects.filter(etat=1,creation__month=2,creation__year=annee_encours).aggregate(tot=Sum('finaltotal'))
        facture_fev = facture_fev['tot']
        if facture_fev == None:
            facture_fev = 0
        else:
            facture_fev = facture_fev

        facture_mars = Facture.objects.filter(etat=1,creation__month=3,creation__year=annee_encours).aggregate(tot=Sum('finaltotal'))
        facture_mars = facture_mars['tot']
        if facture_mars == None:
            facture_mars = 0
        else:
            facture_mars = facture_mars
        
        facture_avr = Facture.objects.filter(etat=1,creation__month=4,creation__year=annee_encours).aggregate(tot=Sum('finaltotal'))
        facture_avr = facture_avr['tot']
        if facture_avr == None:
            facture_avr = 0
        else:
            facture_avr = facture_avr
        
        facture_mai = Facture.objects.filter(etat=1,creation__month=5,creation__year=annee_encours).aggregate(tot=Sum('finaltotal'))
        facture_mai = facture_mai['tot']
        if facture_mai == None:
            facture_mai = 0
        else:
            facture_mai = facture_mai
        
        facture_juin = Facture.objects.filter(etat=1,creation__month=6,creation__year=annee_encours).aggregate(tot=Sum('finaltotal'))
        facture_juin = facture_juin['tot']
        if facture_juin == None:
            facture_juin = 0
        else:
            facture_juin = facture_juin
        
        facture_juil = Facture.objects.filter(etat=1,creation__month=7,creation__year=annee_encours).aggregate(tot=Sum('finaltotal'))
        facture_juil = facture_juil['tot']
        if facture_juil == None:
            facture_juil = 0
        else:
            facture_juil = facture_juil
        
        facture_aout = Facture.objects.filter(etat=1,creation__month=8,creation__year=annee_encours).aggregate(tot=Sum('finaltotal'))
        facture_aout = facture_aout['tot']
        if facture_aout == None:
            facture_aout = 0
        else:
            facture_aout = facture_aout
        
        facture_sept = Facture.objects.filter(etat=1,creation__month=9,creation__year=annee_encours).aggregate(tot=Sum('finaltotal'))
        facture_sept = facture_sept['tot']
        if facture_sept == None:
            facture_sept = 0
        else:
            facture_sept = facture_sept
        
        facture_oct = Facture.objects.filter(etat=1,creation__month=10,creation__year=annee_encours).aggregate(tot=Sum('finaltotal'))
        facture_oct = facture_oct['tot']
        if facture_oct == None:
            facture_oct = 0
        else:
            facture_oct = facture_oct
        
        facture_nov = Facture.objects.filter(etat=1,creation__month=11,creation__year=annee_encours).aggregate(tot=Sum('finaltotal'))
        facture_nov = facture_nov['tot']
        if facture_nov == None:
            facture_nov = 0
        else:
            facture_nov = facture_nov
        
        facture_dec = Facture.objects.filter(etat=1,creation__month=12,creation__year=annee_encours).aggregate(tot=Sum('finaltotal'))
        facture_dec = facture_dec['tot']
        if facture_dec == None:
            facture_dec = 0
        else:
            facture_dec = facture_dec

    ###LOCATIVE
    ####DEPENSE DU MOIS
    depense_du_mois = Depense.objects.filter(creation__month=mois_encours,creation__year=annee_encours).aggregate(tot=Sum('valeur'))
    depense_du_mois = depense_du_mois['tot']
    if depense_du_mois == None:
        depense_du_mois = 0
    else:
        depense_du_mois = depense_du_mois
    
    #CONTRAT INACTIF
    contrat_inactif = Contrat.objects.filter(activecontrat=0).count()
    contrat_actif = Contrat.objects.filter(activecontrat=1).count()
    contrat_termine = Contrat.objects.filter(activecontrat=2).count()

    if countSoftkey == 0:
        start_date = datetime.today()
        date_1 = pd.to_datetime(start_date)
        end_date = date_1+pd.DateOffset(days=20)
        softk = uuid.uuid4()
        Softkeyactive.objects.create(
            keyword = softk,
            datesoft = end_date
        )
        diff_in_hours = 1
    else:
        end_date_soft = Softkeyactive.objects.last().datesoft
        #print(end_date_soft) 
        date_1 = str(datetime.now())
        date_2 = str(end_date_soft)
        n_date_2 = date_2[:19]
        n_date_1 = date_1[:19]
        
        date_format_str = '%Y-%m-%d %H:%M:%S'
        start = datetime.strptime(n_date_1, date_format_str)
        end =   datetime.strptime(n_date_2, date_format_str)
        # Get interval between two timstamps as timedelta object
        diff = end - start
        diff_in_hours = (diff.total_seconds() / 3600)
        diff_in_hours = diff_in_hours /24
        
    
    if diff_in_hours < 0.1:
        all_user = User.objects.filter(is_staff=0)
        for all_u in all_user:
            User.objects.filter(id=all_u.id).update(
                is_active = 0
            )
    else:
        all_user = User.objects.filter(is_staff=0)
        for all_u in all_user:
            User.objects.filter(id=all_u.id).update(
                is_active = 1
            )

    content = {
        'etat':etat,
        'accueil': True,
        'derniere_facture':derniere_facture,
        'facture_gene':facture_gene,
        'facture_paye':facture_paye,
        'facture_imp':facture_imp,
        'mois_encours':tab_mois[mois_encours-1],
        'percentage_paye':round(percentage_paye,2),
        'percentage_impaye':round(percentage_impaye,2),
        'facture_jan':str(facture_jan),
        'facture_fev':str(facture_fev),
        'facture_mars':str(facture_mars),
        'facture_avr':str(facture_avr),
        'facture_mai':str(facture_mai),
        'facture_juin':str(facture_juin),
        'facture_juil':str(facture_juil),
        'facture_aout':str(facture_aout),
        'facture_sept':str(facture_sept),
        'facture_oct':str(facture_oct),
        'facture_nov':str(facture_nov),
        'facture_dec':str(facture_dec),
        'depense_mois': str(depense_mois),
        'facture_paye_str':str(facture_paye),
        'facture_imp_str':str(facture_imp),
        'depense_du_mois':depense_du_mois,
        'contrat_inactif':contrat_inactif,
        'contrat_actif':contrat_actif,
        'contrat_termine':contrat_termine,
        'diff_in_hours':round(diff_in_hours,1)
    }
    return render(request,'gimmo/pages/accueil.html',content)


####EMPLOYE
@login_required(login_url='/')
def employe(request):
    etat = 0
    liste_employe = Employe.objects.filter(d1__gte=1).order_by('creation')

    content = {
        'etat':etat,
        'employe': True,
        'liste_employe':liste_employe
    }
    return render(request,'gimmo/pages/employe/employe.html',content)

@login_required(login_url='/')
def newemploye(request):
    etat = 0
    liste_locative = Locative.objects.filter(etat=1)
    count_tab = Employe.objects.all().count()
    matricule = 'EP26-'+str(count_tab)

    content = {
        'etat':etat,
        'employe': True,
        'liste_locative':liste_locative,
        'matricule':matricule
    }
    return render(request,'gimmo/pages/employe/newemploye.html',content)

@login_required(login_url='/')
def eemploye(request,pk):
    etat = 0
    un_employe = get_object_or_404(Employe, idpub=pk)
    daten = datetime.strptime(str(un_employe.daten), '%Y-%m-%d').strftime('%Y-%m-%d')

    if str(un_employe.dpiece) == '2021-12-14':
        dpiece = ''
    else:
        dpiece = datetime.strptime(str(un_employe.dpiece), '%Y-%m-%d').strftime('%Y-%m-%d')
    
    if str(un_employe.epiece) == '2021-12-14':
        epiece = ''
    else:
        epiece = datetime.strptime(str(un_employe.epiece), '%Y-%m-%d').strftime('%Y-%m-%d')

    content = {
        'etat':etat,
        'employe': True,
        'un_employe':un_employe,
        'daten':daten,
        'dpiece':dpiece,
        'epiece':epiece
    }
    return render(request,'gimmo/pages/employe/eemploye.html',content)

def ajxemp(request):
    etat = 0
    
    if request.method == "POST":
        civilite = request.POST.get('civilite',False)
        nom = request.POST.get('nom',False)
        prenoms = request.POST.get('prenoms',False)
        daten = request.POST.get('daten',False)
        profession = request.POST.get('profession',False)
        adresse = request.POST.get('adresse',False)
        tel = request.POST.get('tel',False)
        naturepiece = request.POST.get('naturepiece',False)
        numpiece = request.POST.get('numpiece',False)
        lpiece = request.POST.get('lpiece',False)
        dpiece = request.POST.get('dpiece',False)
        epiece = request.POST.get('epiece',False)
        statutma = request.POST.get('statutma',False)
        nbenfant = request.POST.get('nbenfant',False)
        typecontrat = request.POST.get('typecontrat',False)
        nomu = request.POST.get('nomu',False)
        prenomsu = request.POST.get('prenomsu',False)
        contactu = request.POST.get('contactu',False)
        pseudo = request.POST.get('pseudo',False)
        mdp = request.POST.get('mdp',False)
        email = request.POST.get('email',False)

        activeemploye = request.POST.get('activeemploye',False)
        if activeemploye == False:
            d5 = 0
        else:
            d5 = activeemploye

        activeproprietaire = request.POST.get('activeproprietaire',False)
        if activeproprietaire == False:
            d6 = 0
        else:
            d6 = activeproprietaire

        activelocataire = request.POST.get('activelocataire',False)
        if activelocataire == False:
            d7 = 0
        else:
            d7 = activelocataire

        activelocative = request.POST.get('activelocative',False)
        if activelocative == False:
            d8 = 0
        else:
            d8 = activelocative

        activebien = request.POST.get('activebien',False)
        if activebien == False:
            d9 = 0
        else:
            d9 = activebien

        activecontrat = request.POST.get('activecontrat',False)
        if activecontrat == False:
            d10 = 0
        else:
            d10 = activecontrat

        activepaiement = request.POST.get('activepaiement',False)
        if activepaiement == False:
            d11 = 0
        else:
            d11 = activepaiement

        activerapport = request.POST.get('activerapport',False)
        if activerapport == False:
            d12 = 0
        else:
            d12 = activerapport

        activesuperadmin = request.POST.get('activesuperadmin',False)
        if activesuperadmin == False:
            d13 = 0
        else:
            d13 = activesuperadmin

        
        if dpiece == '' or dpiece == False:
            dpiece = '2021-12-14'
        else:
            dpiece = dpiece
        
        if epiece == '' or epiece == False:
            epiece = '2021-12-14'
        else:
            epiece = epiece
        
        if daten == '' or daten == False:
            daten = '2021-12-14'
        else:
            daten = daten


        if request.FILES.get('profile', False):
            im1 = request.FILES['profile']
            profile = FileSystemStorage()
            profile = profile.save(im1.name, im1)
        else:
            profile = ""
        
        if Employe.objects.filter(nom=nom,prenoms=prenoms).exists():
            etat = 2
        else:
            count_tab = Employe.objects.all().count()
            idpub = uuid.uuid4()
            idpub = str(idpub).replace("-","")
            publicid = idpub + str(count_tab)
            user = User.objects.create_user(username=pseudo,first_name=nom,last_name=prenoms,password=mdp,email=email)
            Employe.objects.create(
                idpub = publicid,
                civilite = civilite,
                nom = nom,
                prenoms = prenoms,
                daten = daten,
                profession =profession,
                adresse = adresse,
                tel = tel,
                naturepiece = naturepiece,
                numpiece = numpiece,
                lpiece = lpiece,
                dpiece = dpiece,
                epiece = epiece,
                statutma = statutma,
                nbenfant = nbenfant,
                typecontrat = typecontrat,
                nomu = nomu,
                prenomsu = prenomsu,
                contactu = contactu,
                photo = profile,
                d1 = 1,
                d2 = 0,
                d3 = 0,
                d4 = 0,
                d5 = d5,
                d6 = d6,
                d7 = d7,
                d8 = d8,
                d9 = d9,
                d10 = d10,
                d11 = d11,
                d12 = d12,
                d13 = d13,
                d14 = 0,
                user = user,
                creation = datetime.now()
            ).save()
            etat = 1

        
        count_t = Employe.objects.all().count()
        matricule = 'EP26-'+str(count_t)
    
    data = {
        'etat': etat,
        'matricule':matricule
    }
    return JsonResponse(data)


def eajxemp(request):
    etat = 0
    
    if request.method == "POST":
        civilite = request.POST.get('civilite',False)
        nom = request.POST.get('nom',False)
        prenoms = request.POST.get('prenoms',False)
        daten = request.POST.get('daten',False)
        profession = request.POST.get('profession',False)
        adresse = request.POST.get('adresse',False)
        tel = request.POST.get('tel',False)
        naturepiece = request.POST.get('naturepiece',False)
        numpiece = request.POST.get('numpiece',False)
        lpiece = request.POST.get('lpiece',False)
        dpiece = request.POST.get('dpiece',False)
        epiece = request.POST.get('epiece',False)
        statutma = request.POST.get('statutma',False)
        nbenfant = request.POST.get('nbenfant',False)
        typecontrat = request.POST.get('typecontrat',False)
        nomu = request.POST.get('nomu',False)
        prenomsu = request.POST.get('prenomsu',False)
        contactu = request.POST.get('contactu',False)
        idpub = request.POST.get('idpub',False)
        email = request.POST.get('email',False)
        
        activeemploye = request.POST.get('activeemploye',False)
        if activeemploye == False:
            d5 = 0
        else:
            d5 = 1

        activeproprietaire = request.POST.get('activeproprietaire',False)
        if activeproprietaire == False:
            d6 = 0
        else:
            d6 = 1

        activelocataire = request.POST.get('activelocataire',False)
        if activelocataire == False:
            d7 = 0
        else:
            d7 = 1

        activelocative = request.POST.get('activelocative',False)
        if activelocative == False:
            d8 = 0
        else:
            d8 = 1

        activebien = request.POST.get('activebien',False)
        if activebien == False:
            d9 = 0
        else:
            d9 = 1

        activecontrat = request.POST.get('activecontrat',False)
        if activecontrat == False:
            d10 = 0
        else:
            d10 = 1

        activepaiement = request.POST.get('activepaiement',False)
        if activepaiement == False:
            d11 = 0
        else:
            d11 = 1

        activerapport = request.POST.get('activerapport',False)
        if activerapport == False:
            d12 = 0
        else:
            d12 = 1

        activesuperadmin = request.POST.get('activesuperadmin',False)
        if activesuperadmin == False:
            d13 = 0
        else:
            d13 = 1
        
        if dpiece == '' or dpiece == False:
            dpiece = '2021-12-14'
        else:
            dpiece = dpiece
        
        if epiece == '' or epiece == False:
            epiece = '2021-12-14'
        else:
            epiece = epiece
        
        if daten == '' or daten == False:
            daten = '2021-12-14'
        else:
            daten = daten

        un_employe = get_object_or_404(Employe, idpub=idpub)

        if request.FILES.get('profile', False):
            im1 = request.FILES['profile']
            profile = FileSystemStorage()
            profile = profile.save(im1.name, im1)
        else:
            profile = un_employe.photo
        
        Employe.objects.filter(idpub=idpub).update(
            civilite = civilite,
            nom = nom,
            prenoms = prenoms,
            daten = daten,
            profession =profession,
            adresse = adresse,
            tel = tel,
            naturepiece = naturepiece,
            numpiece = numpiece,
            lpiece = lpiece,
            dpiece = dpiece,
            epiece = epiece,
            statutma = statutma,
            nbenfant = nbenfant,
            typecontrat = typecontrat,
            nomu = nomu,
            prenomsu = prenomsu,
            contactu = contactu,
            photo = profile,
            d5 = d5,
            d6 = d6,
            d7 = d7,
            d8 = d8,
            d9 = d9,
            d10 = d10,
            d11 = d11,
            d12 = d12,
            d13 = d13
        )
        User.objects.filter(id=un_employe.user.id).update(
            email=email
        )
        etat = 1
    
    data = {
        'etat': etat
    }
    return JsonResponse(data)

def infoEmploye(request):
    if request.method == 'GET':
        id = request.GET.get('id',False)
        un_employe = get_object_or_404(Employe, idpub=id)
        html_data = """
            <div class="row-view">
                <div class="lg-c12 md-c12 sm-c12 xs-c12">
                    <div class="list-btn">
                        <a href="/pdfunemploye/"""+str(id)+"""" class="a-button" style="--clr:#e91919;">
                           <span class="material-icons-sharp">
                            text_snippet
                            </span>
                            Exporter Pdf
                        </a>
                    </div>
                </div>
            </div><br>
            <div class="row-view">
                <div class="lg-c12 md-c12 sm-c12 xs-c12">
                    <h3 class="cl-primary">
                       Informations sur l'employé
                    </h3>
                </div>
                <div class="lg-c4 md-c4 sm-c3 xs-c6">
                    <div class="info-text">
                        <span class="title-text">Civilité</span>
                        <span class="title-content civilite">"""+str(un_employe.civilite)+"""</span>
                    </div>
                </div>
                <div class="lg-c4 md-c4 sm-c3 xs-c6">
                    <div class="info-text">
                        <span class="title-text">Nom & prénoms</span>
                        <span class="title-content nom">"""+str(un_employe.nom.upper())+' '+str(un_employe.prenoms)+"""</span>
                    </div>
                </div>
                <div class="lg-c4 md-c4 sm-c3 xs-c6">
                    <div class="info-text">
                        <span class="title-text">Date de naissance</span>
                        <span class="title-content daten">"""+str(un_employe.daten)+"""</span>
                    </div>
                </div>
                <div class="lg-c4 md-c4 sm-c3 xs-c6">
                    <div class="info-text">
                        <span class="title-text">Profession</span>
                        <span class="title-content profession">"""+str(un_employe.profession)+"""</span>
                    </div>
                </div>
                <div class="lg-c4 md-c4 sm-c3 xs-c6">
                    <div class="info-text">
                        <span class="title-text">Nature de la pièce</span>
                        <span class="title-content naturepiece">"""+str(un_employe.naturepiece)+"""</span>
                    </div>
                </div>
                <div class="lg-c4 md-c4 sm-c3 xs-c6">
                    <div class="info-text">
                        <span class="title-text">Numéro de la pièce</span>
                        <span class="title-content numpiece">"""+str(un_employe.numpiece)+"""</span>
                    </div>
                </div>
                <div class="lg-c4 md-c4 sm-c3 xs-c6">
                    <div class="info-text">
                        <span class="title-text">Lieu de délivrance</span>
                        <span class="title-content lpiece">"""+str(un_employe.lpiece)+"""</span>
                    </div>
                </div>
                <div class="lg-c4 md-c4 sm-c3 xs-c6">
                    <div class="info-text">
                        <span class="title-text">Date délivrance</span>
                        <span class="title-content dpiece">"""+str(un_employe.dpiece)+"""</span>
                    </div>
                </div>
                <div class="lg-c4 md-c4 sm-c3 xs-c6">
                    <div class="info-text">
                        <span class="title-text">Date d'expiration</span>
                        <span class="title-content epiece">"""+str(un_employe.epiece)+"""</span>
                    </div>
                </div>
                <div class="lg-c4 md-c4 sm-c3 xs-c6">
                    <div class="info-text">
                        <span class="title-text">Adresse</span>
                        <span class="title-content adresse">"""+str(un_employe.adresse)+"""</span>
                    </div>
                </div>
                <div class="lg-c4 md-c4 sm-c3 xs-c6">
                    <div class="info-text">
                        <span class="title-text">Téléphone</span>
                        <span class="title-content tel">"""+str(un_employe.tel)+"""</span>
                    </div>
                </div>
                
                <div class="lg-c4 md-c4 sm-c3 xs-c6">
                    <div class="info-text">
                        <span class="title-text">Type contrat</span>
                        <span class="title-content lieutaf">"""+str(un_employe.typecontrat)+"""</span>
                    </div>
                </div>
                <div class="lg-c12 md-c12 sm-c12 xs-c12">
                    <h3 class="cl-primary">
                       Personne à contacter en cas d'urgence
                    </h3>
                </div>
                <div class="lg-c4 md-c4 sm-c3 xs-c6">
                    <div class="info-text">
                        <span class="title-text">Nom & prénoms</span>
                        <span class="title-content nomu">"""+str(un_employe.nomu.upper())+' '+str(un_employe.prenomsu)+""" </span>
                    </div>
                </div>
                <div class="lg-c4 md-c4 sm-c3 xs-c6">
                    <div class="info-text">
                        <span class="title-text">Contact</span>
                        <span class="title-content contactu">"""+str(un_employe.contactu)+"""</span>
                    </div>
                </div>

                <div class="lg-c12 md-c12 sm-c12 xs-c12">
                    <h3 class="cl-primary">
                       Informations de connexion
                    </h3>
                </div>
                <div class="lg-c4 md-c4 sm-c3 xs-c6">
                    <div class="info-text">
                        <span class="title-text">Nom d'utilisateur</span>
                        <span class="title-content pseudo">"""+str(un_employe.user.username)+"""</span>
                    </div>
                </div>
                <div class="lg-c4 md-c4 sm-c3 xs-c6">
                    <div class="info-text">
                        <span class="title-text">Email</span>
                        <span class="title-content email">"""+str(un_employe.user.email)+"""</span>
                    </div>
                </div>
            </div>
        """
    data = {
        'un_employe':html_data
    }
    return JsonResponse(data)


def pdfemploye(request):
    liste_employe = Employe.objects.filter(d1__gte=1).order_by('creation')
    contentdata = {
        'etablissement': Etablissement.objects.get(id=Etablissement.objects.last().id),
        "date": datetime.now(),
        'filenom':"LISTE_EMPLOYE_"+str(datetime.now()),
        'today': datetime.now(),
        'action': request.user.username,
        'liste_employe' : liste_employe
    }
        
    template = get_template('gimmo/pages/employe/pdf-file.html')
    html = template.render(contentdata)

    result = BytesIO()
    pdf = pisa.pisaDocument(BytesIO(html.encode("utf-8")),result)
    if not pdf.err:
        response = HttpResponse(result.getvalue(),content_type='application/pdf')
        filename = "LISTE_EMPLOYE_"+str(datetime.now())+".pdf"
        response['Content-Disposition'] = "attachment; filename="+filename
        return response
        
    return None

def pdfunemploye(request,pk):
    un_employe = Employe.objects.get(idpub=pk)
    contentdata = {
        'etablissement': Etablissement.objects.get(id=Etablissement.objects.last().id),
        "date": datetime.now(),
        'filenom':"EMPLOYE_"+str(un_employe.nom)+' '+str(un_employe.prenoms),
        'today': datetime.now(),
        'action': request.user.username,
        'un_employe' : un_employe
    }
        
    template = get_template('gimmo/pages/employe/pdf-info.html')
    html = template.render(contentdata)

    result = BytesIO()
    pdf = pisa.pisaDocument(BytesIO(html.encode("utf-8")),result)
    if not pdf.err:
        response = HttpResponse(result.getvalue(),content_type='application/pdf')
        filename = "EMPLOYE_"+str(un_employe.nom)+' '+str(un_employe.prenoms)+".pdf"
        response['Content-Disposition'] = "attachment; filename="+filename
        return response
        
    return None


####PROPRIETAIRE
@login_required(login_url='/')
def proprietaire(request):
    etat = 0
    liste_proprietaire = Proprietaire.objects.all().order_by('creation')

    content = {
        'etat':etat,
        'proprietaire': True,
        'liste_proprietaire':liste_proprietaire
    }
    return render(request,'gimmo/pages/proprietaire/proprietaire.html',content)


def lproprietaire(request,pk):
    etat = 0
    liste_facture = Facture.objects.filter(etat__lte=1,contrat__proprietaire__idpub=pk).order_by('creation')

    totala = Facture.objects.filter(etat__lte=1,contrat__proprietaire__idpub=pk).aggregate(tot=Sum('finaltotal'))
    totala = totala['tot']
    if totala == None:
        totala = 0
    else:
        totala = totala

    totalp = Facture.objects.filter(etat__lte=1,contrat__proprietaire__idpub=pk).aggregate(tot=Sum('payefacture'))
    totalp = totalp['tot']
    if totalp == None:
        totalp = 0
    else:
        totalp = totalp
        
    totalr = Facture.objects.filter(etat__lte=1,contrat__proprietaire__idpub=pk).aggregate(tot=Sum('restefacture'))
    totalr = totalr['tot']
    if totalr == None:
        totalr = 0
    else:
        totalr = totalr

    content = {
        'etat':etat,
        'proprietaire': True,
        'liste_facture':liste_facture,
        'totala':totala,
        'totalp':totalp,
        'totalr':totalr,
        'un_proprietaire': Proprietaire.objects.get(idpub=pk)
    }
    return render(request,'gimmo/pages/proprietaire/lproprietaire.html',content)

def pdfrapportproprietaire(request,pk):
    liste_facture = Facture.objects.filter(etat__lte=1,contrat__proprietaire__idpub=pk).order_by('creation')

    totala = Facture.objects.filter(etat__lte=1,contrat__proprietaire__idpub=pk).aggregate(tot=Sum('finaltotal'))
    totala = totala['tot']
    if totala == None:
        totala = 0
    else:
        totala = totala

    totalp = Facture.objects.filter(etat__lte=1,contrat__proprietaire__idpub=pk).aggregate(tot=Sum('payefacture'))
    totalp = totalp['tot']
    if totalp == None:
        totalp = 0
    else:
        totalp = totalp
        
    totalr = Facture.objects.filter(etat__lte=1,contrat__proprietaire__idpub=pk).aggregate(tot=Sum('restefacture'))
    totalr = totalr['tot']
    if totalr == None:
        totalr = 0
    else:
        totalr = totalr


    contentdata = {
        'etablissement': Etablissement.objects.get(id=Etablissement.objects.last().id),
        "date": datetime.now(),
        'filenom':"RAPPORT_PAIEMENT_"+str(datetime.now()),
        'today': datetime.now(),
        'action': request.user.username,
        'liste_facture':liste_facture,
        'totala':totala,
        'totalp':totalp,
        'totalr':totalr,
        'un_proprietaire': Proprietaire.objects.get(idpub=pk)
    }
        
    template = get_template('gimmo/pages/proprietaire/rapport-pdf.html')
    html = template.render(contentdata)

    result = BytesIO()
    pdf = pisa.pisaDocument(BytesIO(html.encode("utf-8")),result)
    if not pdf.err:
        response = HttpResponse(result.getvalue(),content_type='application/pdf')
        filename = "LISTE_RAPPORT_"+str(datetime.now())+".pdf"
        response['Content-Disposition'] = "attachment; filename="+filename
        return response
        
    return None

@login_required(login_url='/')
def eproprietaire(request,pk):
    etat = 0
    un_proprietaire = get_object_or_404(Proprietaire, idpub=pk)
    daten = datetime.strptime(str(un_proprietaire.datenaiss), '%Y-%m-%d').strftime('%Y-%m-%d')

    if str(un_proprietaire.datedelivrance) == '2021-12-14':
        dated = ''
    else:
        dated = datetime.strptime(str(un_proprietaire.datedelivrance), '%Y-%m-%d').strftime('%Y-%m-%d')
    
    if str(un_proprietaire.dateexpir) == '2021-12-14':
        datee = ''
    else:
        datee = datetime.strptime(str(un_proprietaire.dateexpir), '%Y-%m-%d').strftime('%Y-%m-%d')

    content = {
        'etat':etat,
        'proprietaire': True,
        'un_proprietaire':un_proprietaire,
        'daten':daten,
        'dated':dated,
        'datee':datee
    }
    return render(request,'gimmo/pages/proprietaire/eproprietaire.html',content)

def eajxpro(request):
    etat = 0
    
    if request.method == "POST":
        civilite = request.POST.get('civilite',False)
        nom = request.POST.get('nom',False)
        prenoms = request.POST.get('prenoms',False)
        daten = request.POST.get('daten',False)
        profession = request.POST.get('profession',False)
        lieutaf = request.POST.get('lieutaf',False)
        naturepiece = request.POST.get('naturepiece',False)
        numpiece = request.POST.get('numpiece',False)
        lpiece = request.POST.get('lpiece',False)
        dpiece = request.POST.get('dpiece',False)
        epiece = request.POST.get('epiece',False)
        adresse = request.POST.get('adresse',False)
        ville = request.POST.get('ville',False)
        quartier = request.POST.get('quartier',False)
        telfixe = request.POST.get('telfixe',False)
        tel = request.POST.get('tel',False)
        nomu = request.POST.get('nomu',False)
        prenomsu = request.POST.get('prenomsu',False)
        contactu = request.POST.get('contactu',False)
        email = request.POST.get('email',False)
        idpub = request.POST.get('idpub',False)
       
        if daten == '':
            daten = '2021-12-14'
        else:
            daten = datetime.strptime(daten, '%Y-%m-%d').strftime('%Y-%m-%d')

        if dpiece == '':
            dpiece = '2021-12-14'
        else:
            dpiece = datetime.strptime(dpiece, '%Y-%m-%d').strftime('%Y-%m-%d')

        if epiece == '':
            epiece = '2021-12-14'
        else:
            epiece = datetime.strptime(epiece, '%Y-%m-%d').strftime('%Y-%m-%d')

        un_proprietaire = get_object_or_404(Proprietaire, idpub=idpub)

        if request.FILES.get('profile', False):
            im1 = request.FILES['profile']
            profile = FileSystemStorage()
            profile = profile.save(im1.name, im1)
        else:
            profile = un_proprietaire.photo
        
        Proprietaire.objects.filter(idpub=idpub).update(
            nom = nom,
            prenom = prenoms,
            civilite = civilite,
            datenaiss = daten,
            profession = profession,
            lieutaf = lieutaf,
            naturepiece = naturepiece,
            numpiece = numpiece,
            lieudelivrance = lpiece,
            datedelivrance = dpiece,
            dateexpir = epiece,
            adresse = adresse,
            ville = ville,
            quartier = quartier,
            fixe = telfixe,
            tel = tel,
            nomu = nomu,
            prenomu = prenomsu,
            contactu = contactu,
            photo = profile
        )
        User.objects.filter(id=un_proprietaire.user.id).update(
            email=email
        )
        etat = 1
    
    data = {
        'etat': etat
    }
    return JsonResponse(data)

@login_required(login_url='/')
def newproprietaire(request):
    etat = 0
    count_tab = Proprietaire.objects.all().count()
    matricule = 'P26-'+str(count_tab)

    content = {
        'etat':etat,
        'proprietaire': True,
        'matricule':matricule
    }
    return render(request,'gimmo/pages/proprietaire/newproprietaire.html',content)

def ajxpro(request):
    etat = 0
    
    if request.method == "POST":
        civilite = request.POST.get('civilite',False)
        nom = request.POST.get('nom',False)
        prenoms = request.POST.get('prenoms',False)
        daten = request.POST.get('daten',False)
        profession = request.POST.get('profession',False)
        lieutaf = request.POST.get('lieutaf',False)
        naturepiece = request.POST.get('naturepiece',False)
        numpiece = request.POST.get('numpiece',False)
        lpiece = request.POST.get('lpiece',False)
        dpiece = request.POST.get('dpiece',False)
        epiece = request.POST.get('epiece',False)
        adresse = request.POST.get('adresse',False)
        ville = request.POST.get('ville',False)
        quartier = request.POST.get('quartier',False)
        telfixe = request.POST.get('telfixe',False)
        tel = request.POST.get('tel',False)
        nomu = request.POST.get('nomu',False)
        prenomsu = request.POST.get('prenomsu',False)
        contactu = request.POST.get('contactu',False)
        pseudo = request.POST.get('pseudo',False)
        mdp = request.POST.get('mdp',False)
        email = request.POST.get('email',False)

        if dpiece == '' or dpiece == False:
            dpiece = '2021-12-14'
        else:
            dpiece = dpiece
        
        if epiece == '' or epiece == False:
            epiece = '2021-12-14'
        else:
            epiece = epiece
        
        if daten == '' or daten == False:
            daten = '2021-12-14'
        else:
            daten = daten


        if request.FILES.get('profile', False):
            im1 = request.FILES['profile']
            profile = FileSystemStorage()
            profile = profile.save(im1.name, im1)
        else:
            profile = ""
        
        if Proprietaire.objects.filter(nom=nom,prenom=prenoms).exists():
            etat = 2
        else:
            count_tab = Proprietaire.objects.all().count()
            idpub = uuid.uuid4()
            idpub = str(idpub).replace("-","")
            publicid = idpub + str(count_tab)

            user = User.objects.create_user(username=pseudo,first_name=nom,last_name=prenoms,password=mdp,email=email)
            Proprietaire.objects.create(
                idpub = publicid,
                nom = nom,
                prenom = prenoms,
                civilite = civilite,
                datenaiss = daten,
                profession = profession,
                lieutaf = lieutaf,
                naturepiece = naturepiece,
                numpiece = numpiece,
                lieudelivrance = lpiece,
                datedelivrance = dpiece,
                dateexpir = epiece,
                adresse = adresse,
                ville = ville,
                quartier = quartier,
                fixe = telfixe,
                tel = tel,
                nomu = nomu,
                prenomu = prenomsu,
                contactu = contactu,
                photo = profile,
                d1 = 1,
                d2 = 0,
                d3 = 0,
                d4 = 0,
                d5 = 0,
                d6 = 0,
                user = user,
                creation = datetime.now()
            ).save()
            etat = 1

        
        count_t = Proprietaire.objects.all().count()
        matricule = 'P26-'+str(count_t)
    
    data = {
        'etat': etat,
        'matricule':matricule
    }
    return JsonResponse(data)

def infoProprietaire(request):
    if request.method == 'GET':
        id = request.GET.get('id',False)
        un_proprietaire = get_object_or_404(Proprietaire, idpub=id)
        html_data = """
            <div class="row-view">
                <div class="lg-c12 md-c12 sm-c12 xs-c12">
                    <div class="list-btn">
                        <a href="/pdfunproprietaire/"""+str(id)+"""" class="a-button" style="--clr:#e91919;">
                           <span class="material-icons-sharp">
                            text_snippet
                            </span>
                            Exporter Pdf
                        </a>
                    </div>
                </div>
            </div><br>
            <div class="row-view">
            <div class="lg-c12 md-c12 sm-c12 xs-c12">
                    <h3 class="cl-primary">
                       Informations personnelles
                    </h3>
                </div>
                <div class="lg-c4 md-c4 sm-c3 xs-c6">
                    <div class="info-text">
                        <span class="title-text">Civilité</span>
                        <span class="title-content civilite">"""+str(un_proprietaire.civilite)+"""</span>
                    </div>
                </div>
                <div class="lg-c4 md-c4 sm-c3 xs-c6">
                    <div class="info-text">
                        <span class="title-text">Nom & prénoms</span>
                        <span class="title-content nom">"""+str(un_proprietaire.nom.upper())+' '+str(un_proprietaire.prenom)+"""</span>
                    </div>
                </div>
                <div class="lg-c4 md-c4 sm-c3 xs-c6">
                    <div class="info-text">
                        <span class="title-text">Date de naissance</span>
                        <span class="title-content daten">"""+str(un_proprietaire.datenaiss)+"""</span>
                    </div>
                </div>
                <div class="lg-c4 md-c4 sm-c3 xs-c6">
                    <div class="info-text">
                        <span class="title-text">Profession</span>
                        <span class="title-content profession">"""+str(un_proprietaire.profession)+"""</span>
                    </div>
                </div>
                <div class="lg-c4 md-c4 sm-c3 xs-c6">
                    <div class="info-text">
                        <span class="title-text">Lieu de travail</span>
                        <span class="title-content lieutaf">"""+str(un_proprietaire.lieutaf)+"""</span>
                    </div>
                </div>
                <div class="lg-c4 md-c4 sm-c3 xs-c6">
                    <div class="info-text">
                        <span class="title-text">Nature de la pièce</span>
                        <span class="title-content naturepiece">"""+str(un_proprietaire.naturepiece)+"""</span>
                    </div>
                </div>
                <div class="lg-c4 md-c4 sm-c3 xs-c6">
                    <div class="info-text">
                        <span class="title-text">Numéro de la pièce</span>
                        <span class="title-content numpiece">"""+str(un_proprietaire.numpiece)+"""</span>
                    </div>
                </div>
                <div class="lg-c4 md-c4 sm-c3 xs-c6">
                    <div class="info-text">
                        <span class="title-text">Lieu de délivrance</span>
                        <span class="title-content lpiece">"""+str(un_proprietaire.lieudelivrance)+"""</span>
                    </div>
                </div>
                <div class="lg-c4 md-c4 sm-c3 xs-c6">
                    <div class="info-text">
                        <span class="title-text">Date délivrance</span>
                        <span class="title-content dpiece">"""+str(un_proprietaire.datedelivrance)+"""</span>
                    </div>
                </div>
                <div class="lg-c4 md-c4 sm-c3 xs-c6">
                    <div class="info-text">
                        <span class="title-text">Date d'expiration</span>
                        <span class="title-content epiece">"""+str(un_proprietaire.dateexpir)+"""</span>
                    </div>
                </div>
                <div class="lg-c4 md-c4 sm-c3 xs-c6">
                    <div class="info-text">
                        <span class="title-text">Adresse</span>
                        <span class="title-content adresse">"""+str(un_proprietaire.adresse)+"""</span>
                    </div>
                </div>
                <div class="lg-c4 md-c4 sm-c3 xs-c6">
                    <div class="info-text">
                        <span class="title-text">Ville</span>
                        <span class="title-content ville">"""+str(un_proprietaire.ville)+"""</span>
                    </div>
                </div>
                <div class="lg-c4 md-c4 sm-c3 xs-c6">
                    <div class="info-text">
                        <span class="title-text">Quartier</span>
                        <span class="title-content quartier">"""+str(un_proprietaire.quartier)+"""</span>
                    </div>
                </div>
                <div class="lg-c4 md-c4 sm-c3 xs-c6">
                    <div class="info-text">
                        <span class="title-text">Téléphone fixe</span>
                        <span class="title-content telfixe">"""+str(un_proprietaire.fixe)+"""</span>
                    </div>
                </div>
                <div class="lg-c4 md-c4 sm-c3 xs-c6">
                    <div class="info-text">
                        <span class="title-text">Téléphone</span>
                        <span class="title-content tel">"""+str(un_proprietaire.tel)+"""</span>
                    </div>
                </div>
                <div class="lg-c12 md-c12 sm-c12 xs-c12">
                    <h3 class="cl-primary">
                       Personne à contacter en cas d'urgence
                    </h3>
                </div>
                <div class="lg-c4 md-c4 sm-c3 xs-c6">
                    <div class="info-text">
                        <span class="title-text">Nom & prénoms</span>
                        <span class="title-content nomu">"""+str(un_proprietaire.nomu.upper())+' '+str(un_proprietaire.prenomu)+""" </span>
                    </div>
                </div>
                <div class="lg-c4 md-c4 sm-c3 xs-c6">
                    <div class="info-text">
                        <span class="title-text">Contact</span>
                        <span class="title-content contactu">"""+str(un_proprietaire.contactu)+"""</span>
                    </div>
                </div>

                <div class="lg-c12 md-c12 sm-c12 xs-c12">
                    <h3 class="cl-primary">
                       Informations de connexion
                    </h3>
                </div>
                <div class="lg-c4 md-c4 sm-c3 xs-c6">
                    <div class="info-text">
                        <span class="title-text">Nom d'utilisateur</span>
                        <span class="title-content pseudo">"""+str(un_proprietaire.user.username)+"""</span>
                    </div>
                </div>
                <div class="lg-c4 md-c4 sm-c3 xs-c6">
                    <div class="info-text">
                        <span class="title-text">Email</span>
                        <span class="title-content email">"""+str(un_proprietaire.user.email)+"""</span>
                    </div>
                </div>
            </div>
        """
    data = {
        'un_proprietaire':html_data
    }
    return JsonResponse(data)


def desProprietaire(request):
    if request.method == 'GET':
        id = request.GET.get('id',False)
        un_proprietaire = get_object_or_404(Proprietaire, idpub=id)
        info_proprietaire = un_proprietaire.nom.upper()+' '+un_proprietaire.prenom

        if un_proprietaire.d1 == 1:
            etat = 0
            text = "Confirmer la désactivation du propriétaire <b>"""+info_proprietaire+"</b>"
        else:
            etat = 1
            text = "Confirmer l'activation du propriétaire <b>"""+info_proprietaire+"</b>"

        #Locataire.objects.filter(idpub=id).update(
        #    d1 = etat
        #)
    data = {
        'text': text
    }
    return JsonResponse(data)

def delProprietaire(request):
    if request.method == 'GET':
        id = request.GET.get('delproprietaire',False)
        un_proprietaire = get_object_or_404(Proprietaire, idpub=id)
        info_proprietaire = un_proprietaire.nom.upper()+' '+un_proprietaire.prenom

        if un_proprietaire.d1 == 1:
            etat = 0
            text = "Confirmer la désactivation du proprietaire <b>"""+info_proprietaire+"</b>"
        else:
            etat = 1
            text = "Confirmer l'activation du proprietaire <b>"""+info_proprietaire+"</b>"

        Proprietaire.objects.filter(idpub=id).update(
            d1 = etat
        )
    data = {
        'text': text
    }
    return JsonResponse(data)


def pdfproprietaire(request):
    liste_proprietaire = Proprietaire.objects.all().order_by('creation')
    contentdata = {
        'etablissement': Etablissement.objects.get(id=Etablissement.objects.last().id),
        "date": datetime.now(),
        'filenom':"LISTE_PROPRIETAIRE_"+str(datetime.now()),
        'today': datetime.now(),
        'action': request.user.username,
        'liste_proprietaire' : liste_proprietaire
    }
        
    template = get_template('gimmo/pages/proprietaire/pdf-file.html')
    html = template.render(contentdata)

    result = BytesIO()
    pdf = pisa.pisaDocument(BytesIO(html.encode("utf-8")),result)
    if not pdf.err:
        response = HttpResponse(result.getvalue(),content_type='application/pdf')
        filename = "LISTE_PROPRIETAIRE_"+str(datetime.now())+".pdf"
        response['Content-Disposition'] = "attachment; filename="+filename
        return response
        
    return None

def pdfunproprietaire(request,pk):
    un_proprietaire = Proprietaire.objects.get(idpub=pk)
    contentdata = {
        'etablissement': Etablissement.objects.get(id=Etablissement.objects.last().id),
        "date": datetime.now(),
        'filenom':"PROPRIETAIRE_"+str(un_proprietaire.nom)+' '+str(un_proprietaire.prenom),
        'today': datetime.now(),
        'action': request.user.username,
        'un_proprietaire' : un_proprietaire
    }
        
    template = get_template('gimmo/pages/proprietaire/pdf-info.html')
    html = template.render(contentdata)

    result = BytesIO()
    pdf = pisa.pisaDocument(BytesIO(html.encode("utf-8")),result)
    if not pdf.err:
        response = HttpResponse(result.getvalue(),content_type='application/pdf')
        filename = "PROPRIETAIRE_"+str(un_proprietaire.nom)+' '+str(un_proprietaire.prenom)+".pdf"
        response['Content-Disposition'] = "attachment; filename="+filename
        return response
        
    return None

####locataire
@login_required(login_url='/')
def locataire(request):
    etat = 0
    if Proprietaire.objects.filter(user=request.user).exists():
        liste_locataire = Contrat.objects.values('locataire','locataire__nom','locataire__raisonsocial','locataire__tel','locataire__creation','locataire__idpub','locataire__prenom','locataire__user__username','locataire__d1').annotate(dcount=Count('locataire')).filter(proprietaire_id=Proprietaire.objects.get(user=request.user).id).order_by()
        etat = 1
    else:
        liste_locataire = Locataire.objects.all().order_by('creation')

    content = {
        'etat':etat,
        'locataire': True,
        'liste_locataire':liste_locataire
    }
    return render(request,'gimmo/pages/locataire/locataire.html',content)

def llocataire(request,pk):
    etat = 0
    liste_facture = Facture.objects.filter(etat__lte=1,locataire__idpub=pk).order_by('creation')

    totala = Facture.objects.filter(etat__lte=1,locataire__idpub=pk).aggregate(tot=Sum('finaltotal'))
    totala = totala['tot']
    if totala == None:
        totala = 0
    else:
        totala = totala

    totalp = Facture.objects.filter(etat__lte=1,locataire__idpub=pk).aggregate(tot=Sum('payefacture'))
    totalp = totalp['tot']
    if totalp == None:
        totalp = 0
    else:
        totalp = totalp
    
    totalr = Facture.objects.filter(etat__lte=1,locataire__idpub=pk).aggregate(tot=Sum('restefacture'))
    totalr = totalr['tot']
    if totalr == None:
        totalr = 0
    else:
        totalr = totalr
    

    content = {
        'etat':etat,
        'locataire': True,
        'liste_facture':liste_facture,
        'totala':totala,
        'totalp':totalp,
        'totalr':totalr,
        'un_locataire': Locataire.objects.get(idpub=pk)
    }
    return render(request,'gimmo/pages/locataire/llocataire.html',content)

def pdfrapportlocataire(request,pk):
    liste_facture = Facture.objects.filter(etat__lte=1,locataire__idpub=pk).order_by('creation')

    totala = Facture.objects.filter(etat__lte=1,locataire__idpub=pk).aggregate(tot=Sum('finaltotal'))
    totala = totala['tot']
    if totala == None:
        totala = 0
    else:
        totala = totala

    totalp = Facture.objects.filter(etat__lte=1,locataire__idpub=pk).aggregate(tot=Sum('payefacture'))
    totalp = totalp['tot']
    if totalp == None:
        totalp = 0
    else:
        totalp = totalp
    
    totalr = Facture.objects.filter(etat__lte=1,locataire__idpub=pk).aggregate(tot=Sum('restefacture'))
    totalr = totalr['tot']
    if totalr == None:
        totalr = 0
    else:
        totalr = totalr

    contentdata = {
        'etablissement': Etablissement.objects.get(id=Etablissement.objects.last().id),
        "date": datetime.now(),
        'filenom':"RAPPORT_PAIEMENT_"+str(datetime.now()),
        'today': datetime.now(),
        'action': request.user.username,
        'liste_facture':liste_facture,
        'totala':totala,
        'totalp':totalp,
        'totalr':totalr,
        'un_locataire': Locataire.objects.get(idpub=pk)
    }
        
    template = get_template('gimmo/pages/locataire/rapport-pdf.html')
    html = template.render(contentdata)

    result = BytesIO()
    pdf = pisa.pisaDocument(BytesIO(html.encode("utf-8")),result)
    if not pdf.err:
        response = HttpResponse(result.getvalue(),content_type='application/pdf')
        filename = "LISTE_RAPPORT_"+str(datetime.now())+".pdf"
        response['Content-Disposition'] = "attachment; filename="+filename
        return response
        
    return None

@login_required(login_url='/')
def newlocataire(request):
    etat = 0
    liste_locative = Locative.objects.filter(etat=1)
    count_tab = Locataire.objects.all().count()
    matricule = 'L26-'+str(count_tab)

    content = {
        'etat':etat,
        'locataire': True,
        'liste_locative':liste_locative,
        'matricule':matricule
    }
    return render(request,'gimmo/pages/locataire/newlocataire.html',content)

@login_required(login_url='/')
def elocataire(request,pk):
    etat = 0
    un_locataire = get_object_or_404(Locataire, idpub=pk)
    daten = datetime.strptime(str(un_locataire.datenaiss), '%Y-%m-%d').strftime('%Y-%m-%d')

    if str(un_locataire.datedelivrance) == '2021-12-14':
        dated = ''
    else:
        dated = datetime.strptime(str(un_locataire.datedelivrance), '%Y-%m-%d').strftime('%Y-%m-%d')
    
    if str(un_locataire.dateexpir) == '2021-12-14':
        datee = ''
    else:
        datee = datetime.strptime(str(un_locataire.dateexpir), '%Y-%m-%d').strftime('%Y-%m-%d')
    

    content = {
        'etat':etat,
        'locataire': True,
        'un_locataire':un_locataire,
        'daten':daten,
        'dated':dated,
        'datee':datee,
        'lenraisonsocial':len(un_locataire.raisonsocial)
    }
    return render(request,'gimmo/pages/locataire/elocataire.html',content)

def ajxloc(request):
    etat = 0
    
    if request.method == "POST":
        civilite = request.POST.get('civilite',False)
        nom = request.POST.get('nom',False)
        prenoms = request.POST.get('prenoms',False)
        daten = request.POST.get('daten',False)
        profession = request.POST.get('profession',False)
        lieutaf = request.POST.get('lieutaf',False)
        naturepiece = request.POST.get('naturepiece',False)
        numpiece = request.POST.get('numpiece',False)
        lpiece = request.POST.get('lpiece',False)
        dpiece = request.POST.get('dpiece',False)
        epiece = request.POST.get('epiece',False)
        statutma = request.POST.get('statutma',False)
        nbenfant = request.POST.get('nbenfant',False)
        adresse = request.POST.get('adresse',False)
        adresseentre = request.POST.get('adresseentre',False)
        telfixe = request.POST.get('telfixe',False)
        tel = request.POST.get('tel',False)
        nomu = request.POST.get('nomu',False)
        prenomsu = request.POST.get('prenomsu',False)
        contactu = request.POST.get('contactu',False)
        pseudo = request.POST.get('pseudo',False)
        mdp = request.POST.get('mdp',False)
        raisonsocial = request.POST.get('raisonsocial',False)
        email = request.POST.get('email',False)
        formejuridique = request.POST.get('formejuridique',False)
        comptecontribuable = request.POST.get('comptecontribuable',False)
        registrecommerce = request.POST.get('registrecommerce',False)
        siege = request.POST.get('siege',False)
        secteur = request.POST.get('secteur',False)
        contactentre = request.POST.get('contactentre',False)
        adresseentre = request.POST.get('adresseentre',False)
        
        if dpiece == '' or dpiece == False:
            dpiece = '2021-12-14'
        else:
            dpiece = dpiece
        
        if epiece == '' or epiece == False:
            epiece = '2021-12-14'
        else:
            epiece = epiece
        
        if daten == '' or daten == False:
            daten = '2021-12-14'
        else:
            daten = daten


        if request.FILES.get('profile', False):
            im1 = request.FILES['profile']
            profile = FileSystemStorage()
            profile = profile.save(im1.name, im1)
        else:
            profile = ""
        
        if Locataire.objects.filter(nom=nom,prenom=prenoms).exists():
            etat = 2
        else:
            count_tab = Locataire.objects.all().count()
            idpub = uuid.uuid4()
            idpub = str(idpub).replace("-","")
            publicid = idpub + str(count_tab)
            user = User.objects.create_user(username=pseudo,first_name=nom,last_name=prenoms,password=mdp,email=email)
            Locataire.objects.create(
                idpub = publicid,
                raisonsocial = raisonsocial,
                formejuridique = formejuridique,
                comptecontribuable = comptecontribuable,
                registrecommerce = registrecommerce,
                siege = siege,
                secteur = secteur,
                contactentre = contactentre,
                adresseentre = adresseentre,
                nom = nom,
                prenom = prenoms,
                civilite = civilite,
                statumat = statutma,
                nbenfant = nbenfant,
                datenaiss = daten,
                profession = profession,
                lieutaf = lieutaf,
                naturepiece = naturepiece,
                numpiece = numpiece,
                lieudelivrance = lpiece,
                datedelivrance = dpiece,
                dateexpir = epiece,
                adresse = adresse,
                fixe = telfixe,
                tel = tel,
                nomu = nomu,
                prenomu = prenomsu,
                contactu = contactu,
                photo = profile,
                d1 = 1,
                d2 = 0,
                d3 = 0,
                d4 = 0,
                d5 = 0,
                d6 = 0,
                user = user,
                creation = datetime.now()
            ).save()
            etat = 1

        
        count_t = Locataire.objects.all().count()
        matricule = 'L26-'+str(count_t)
    
    data = {
        'etat': etat,
        'matricule':matricule
    }
    return JsonResponse(data)


def eajxloc(request):
    etat = 0
    
    if request.method == "POST":
        civilite = request.POST.get('civilite',False)
        nom = request.POST.get('nom',False)
        prenoms = request.POST.get('prenoms',False)
        daten = request.POST.get('daten',False)
        profession = request.POST.get('profession',False)
        lieutaf = request.POST.get('lieutaf',False)
        naturepiece = request.POST.get('naturepiece',False)
        numpiece = request.POST.get('numpiece',False)
        lpiece = request.POST.get('lpiece',False)
        dpiece = request.POST.get('dpiece',False)
        epiece = request.POST.get('epiece',False)
        statutma = request.POST.get('statutma',False)
        nbenfant = request.POST.get('nbenfant',False)
        adresse = request.POST.get('adresse',False)
        adresseentre = request.POST.get('adresseentre',False)
        telfixe = request.POST.get('telfixe',False)
        tel = request.POST.get('tel',False)
        nomu = request.POST.get('nomu',False)
        prenomsu = request.POST.get('prenomsu',False)
        contactu = request.POST.get('contactu',False)
        raisonsocial = request.POST.get('raisonsocial',False)
        email = request.POST.get('email',False)
        formejuridique = request.POST.get('formejuridique',False)
        comptecontribuable = request.POST.get('comptecontribuable',False)
        registrecommerce = request.POST.get('registrecommerce',False)
        siege = request.POST.get('siege',False)
        secteur = request.POST.get('secteur',False)
        contactentre = request.POST.get('contactentre',False)
        idpub = request.POST.get('idpub',False)
        
        
        

        if daten == '':
            daten = '2021-12-14'
        else:
            daten = datetime.strptime(daten, '%Y-%m-%d').strftime('%Y-%m-%d')
        
        if dpiece == '':
            dpiece = '2021-12-14'
        else:
            dpiece = datetime.strptime(dpiece, '%Y-%m-%d').strftime('%Y-%m-%d')
        
        if epiece == '':
            epiece = '2021-12-14'
        else:
            epiece = datetime.strptime(epiece, '%Y-%m-%d').strftime('%Y-%m-%d')

        un_locataire = get_object_or_404(Locataire, idpub=idpub)

        if request.FILES.get('profile', False):
            im1 = request.FILES['profile']
            profile = FileSystemStorage()
            profile = profile.save(im1.name, im1)
        else:
            profile = un_locataire.photo
        
        Locataire.objects.filter(idpub=idpub).update(
            raisonsocial = raisonsocial,
            formejuridique = formejuridique,
            comptecontribuable = comptecontribuable,
            registrecommerce = registrecommerce,
            siege = siege,
            secteur = secteur,
            contactentre = contactentre,
            adresseentre = adresseentre,
            nom = nom,
            prenom = prenoms,
            civilite = civilite,
            statumat = statutma,
            nbenfant = nbenfant,
            datenaiss = daten,
            profession = profession,
            lieutaf = lieutaf,
            naturepiece = naturepiece,
            numpiece = numpiece,
            lieudelivrance = lpiece,
            datedelivrance = dpiece,
            dateexpir = epiece,
            adresse = adresse,
            fixe = telfixe,
            tel = tel,
            nomu = nomu,
            prenomu = prenomsu,
            contactu = contactu,
            photo = profile
        )
        User.objects.filter(id=un_locataire.user.id).update(
            email=email
        )
        etat = 1
    
    data = {
        'etat': etat
    }
    return JsonResponse(data)


def infoLocataire(request):
    if request.method == 'GET':
        id = request.GET.get('id',False)
        un_locataire = get_object_or_404(Locataire, idpub=id)
        html_data = """
            <div class="row-view">
                <div class="lg-c12 md-c12 sm-c12 xs-c12">
                    <div class="list-btn">
                        <a href="/pdfunlocataire/"""+str(id)+""""  class="a-button" style="--clr:#e91919;">
                           <span class="material-icons-sharp">
                            text_snippet
                            </span>
                            Exporter Pdf
                        </a>
                    </div>
                </div>
            </div><br>
            <div class="row-view">
                <div class="lg-c12 md-c12 sm-c12 xs-c12">
                    <h3 class="cl-primary">
                       Informations sur l'entreprise
                    </h3>
                </div>
                <div class="lg-c4 md-c4 sm-c3 xs-c6">
                    <div class="info-text">
                        <span class="title-text">Raison sociale</span>
                        <span class="title-content">"""+str(un_locataire.raisonsocial)+"""</span>
                    </div>
                </div>
                <div class="lg-c4 md-c4 sm-c3 xs-c6">
                    <div class="info-text">
                        <span class="title-text">Forme juridique</span>
                        <span class="title-content">"""+str(un_locataire.formejuridique)+"""</span>
                    </div>
                </div>
                <div class="lg-c4 md-c4 sm-c3 xs-c6">
                    <div class="info-text">
                        <span class="title-text">Compte contribuable</span>
                        <span class="title-content">"""+str(un_locataire.comptecontribuable)+"""</span>
                    </div>
                </div>
                <div class="lg-c4 md-c4 sm-c3 xs-c6">
                    <div class="info-text">
                        <span class="title-text">Régistre commerce</span>
                        <span class="title-content">"""+str(un_locataire.registrecommerce)+"""</span>
                    </div>
                </div>
                <div class="lg-c4 md-c4 sm-c3 xs-c6">
                    <div class="info-text">
                        <span class="title-text">Siège social</span>
                        <span class="title-content">"""+str(un_locataire.siege)+"""</span>
                    </div>
                </div>
                <div class="lg-c4 md-c4 sm-c3 xs-c6">
                    <div class="info-text">
                        <span class="title-text">Adresse</span>
                        <span class="title-content">"""+str(un_locataire.adresseentre)+"""</span>
                    </div>
                </div>
                <div class="lg-c4 md-c4 sm-c3 xs-c6">
                    <div class="info-text">
                        <span class="title-text">Contact</span>
                        <span class="title-content">"""+str(un_locataire.contactentre)+"""</span>
                    </div>
                </div>
                <div class="lg-c4 md-c4 sm-c3 xs-c6">
                    <div class="info-text">
                        <span class="title-text">Secteur d'activité</span>
                        <span class="title-content">"""+str(un_locataire.secteur)+"""</span>
                    </div>
                </div>
                

                <div class="lg-c12 md-c12 sm-c12 xs-c12">
                    <h3 class="cl-primary">
                       Informations sur le locataire
                    </h3>
                </div>
                <div class="lg-c4 md-c4 sm-c3 xs-c6">
                    <div class="info-text">
                        <span class="title-text">Civilité</span>
                        <span class="title-content civilite">"""+str(un_locataire.civilite)+"""</span>
                    </div>
                </div>
                <div class="lg-c4 md-c4 sm-c3 xs-c6">
                    <div class="info-text">
                        <span class="title-text">Nom & prénoms</span>
                        <span class="title-content nom">"""+str(un_locataire.nom.upper())+' '+str(un_locataire.prenom)+"""</span>
                    </div>
                </div>
                <div class="lg-c4 md-c4 sm-c3 xs-c6">
                    <div class="info-text">
                        <span class="title-text">Date de naissance</span>
                        <span class="title-content daten">"""+str(un_locataire.datenaiss)+"""</span>
                    </div>
                </div>
                <div class="lg-c4 md-c4 sm-c3 xs-c6">
                    <div class="info-text">
                        <span class="title-text">Profession</span>
                        <span class="title-content profession">"""+str(un_locataire.profession)+"""</span>
                    </div>
                </div>
                <div class="lg-c4 md-c4 sm-c3 xs-c6">
                    <div class="info-text">
                        <span class="title-text">Lieu de travail</span>
                        <span class="title-content lieutaf">"""+str(un_locataire.lieutaf)+"""</span>
                    </div>
                </div>
                <div class="lg-c4 md-c4 sm-c3 xs-c6">
                    <div class="info-text">
                        <span class="title-text">Nature de la pièce</span>
                        <span class="title-content naturepiece">"""+str(un_locataire.naturepiece)+"""</span>
                    </div>
                </div>
                <div class="lg-c4 md-c4 sm-c3 xs-c6">
                    <div class="info-text">
                        <span class="title-text">Numéro de la pièce</span>
                        <span class="title-content numpiece">"""+str(un_locataire.numpiece)+"""</span>
                    </div>
                </div>
                <div class="lg-c4 md-c4 sm-c3 xs-c6">
                    <div class="info-text">
                        <span class="title-text">Lieu de délivrance</span>
                        <span class="title-content lpiece">"""+str(un_locataire.lieudelivrance)+"""</span>
                    </div>
                </div>
                <div class="lg-c4 md-c4 sm-c3 xs-c6">
                    <div class="info-text">
                        <span class="title-text">Date délivrance</span>
                        <span class="title-content dpiece">"""+str(un_locataire.datedelivrance)+"""</span>
                    </div>
                </div>
                <div class="lg-c4 md-c4 sm-c3 xs-c6">
                    <div class="info-text">
                        <span class="title-text">Date d'expiration</span>
                        <span class="title-content epiece">"""+str(un_locataire.dateexpir)+"""</span>
                    </div>
                </div>
                <div class="lg-c4 md-c4 sm-c3 xs-c6">
                    <div class="info-text">
                        <span class="title-text">Adresse</span>
                        <span class="title-content adresse">"""+str(un_locataire.adresse)+"""</span>
                    </div>
                </div>
                <div class="lg-c4 md-c4 sm-c3 xs-c6">
                    <div class="info-text">
                        <span class="title-text">Téléphone</span>
                        <span class="title-content tel">"""+str(un_locataire.tel)+"""</span>
                    </div>
                </div>
                <div class="lg-c12 md-c12 sm-c12 xs-c12">
                    <h3 class="cl-primary">
                       Personne à contacter en cas d'urgence
                    </h3>
                </div>
                <div class="lg-c4 md-c4 sm-c3 xs-c6">
                    <div class="info-text">
                        <span class="title-text">Nom & prénoms</span>
                        <span class="title-content nomu">"""+str(un_locataire.nomu.upper())+' '+str(un_locataire.prenomu)+""" </span>
                    </div>
                </div>
                <div class="lg-c4 md-c4 sm-c3 xs-c6">
                    <div class="info-text">
                        <span class="title-text">Contact</span>
                        <span class="title-content contactu">"""+str(un_locataire.contactu)+"""</span>
                    </div>
                </div>

                <div class="lg-c12 md-c12 sm-c12 xs-c12">
                    <h3 class="cl-primary">
                       Informations de connexion
                    </h3>
                </div>
                <div class="lg-c4 md-c4 sm-c3 xs-c6">
                    <div class="info-text">
                        <span class="title-text">Nom d'utilisateur</span>
                        <span class="title-content pseudo">"""+str(un_locataire.user.username)+"""</span>
                    </div>
                </div>
                <div class="lg-c4 md-c4 sm-c3 xs-c6">
                    <div class="info-text">
                        <span class="title-text">Email</span>
                        <span class="title-content email">"""+str(un_locataire.user.email)+"""</span>
                    </div>
                </div>
            </div>
        """
    data = {
        'un_locataire':html_data
    }
    return JsonResponse(data)

def desLocataire(request):
    if request.method == 'GET':
        id = request.GET.get('id',False)
        un_locataire = get_object_or_404(Locataire, idpub=id)
        info_locataire = un_locataire.nom.upper()+' '+un_locataire.prenom

        if un_locataire.d1 == 1:
            etat = 0
            text = "Confirmer la désactivation du locataire <b>"""+info_locataire+"</b>"
        else:
            etat = 1
            text = "Confirmer l'activation du locataire <b>"""+info_locataire+"</b>"

        #Locataire.objects.filter(idpub=id).update(
        #    d1 = etat
        #)
    data = {
        'text': text
    }
    return JsonResponse(data)

def delLocataire(request):
    if request.method == 'GET':
        id = request.GET.get('dellocataire',False)
        un_locataire = get_object_or_404(Locataire, idpub=id)
        info_locataire = un_locataire.nom.upper()+' '+un_locataire.prenom

        if un_locataire.d1 == 1:
            etat = 0
            text = "Confirmer la désactivation du locataire <b>"""+info_locataire+"</b>"
        else:
            etat = 1
            text = "Confirmer l'activation du locataire <b>"""+info_locataire+"</b>"

        Locataire.objects.filter(idpub=id).update(
            d1 = etat
        )
    data = {
        'text': text
    }
    return JsonResponse(data)


def pdflocataire(request):
    liste_locataire = Locataire.objects.all().order_by('creation')
    contentdata = {
        'etablissement': Etablissement.objects.get(id=Etablissement.objects.last().id),
        "date": datetime.now(),
        'filenom':"LISTE_LOCATAIRE_"+str(datetime.now()),
        'today': datetime.now(),
        'action': request.user.username,
        'liste_locataire' : liste_locataire
    }
        
    template = get_template('gimmo/pages/locataire/pdf-file.html')
    html = template.render(contentdata)

    result = BytesIO()
    pdf = pisa.pisaDocument(BytesIO(html.encode("utf-8")),result)
    if not pdf.err:
        response = HttpResponse(result.getvalue(),content_type='application/pdf')
        filename = "LISTE_LOCATAIRE_"+str(datetime.now())+".pdf"
        response['Content-Disposition'] = "attachment; filename="+filename
        return response
        
    return None

def pdfunlocataire(request,pk):
    un_locataire = Locataire.objects.get(idpub=pk)
    contentdata = {
        'etablissement': Etablissement.objects.get(id=Etablissement.objects.last().id),
        "date": datetime.now(),
        'filenom':"LOCATAIRE_"+str(un_locataire.nom)+' '+str(un_locataire.prenom),
        'today': datetime.now(),
        'action': request.user.username,
        'un_locataire' : un_locataire
    }
        
    template = get_template('gimmo/pages/locataire/pdf-info.html')
    html = template.render(contentdata)

    result = BytesIO()
    pdf = pisa.pisaDocument(BytesIO(html.encode("utf-8")),result)
    if not pdf.err:
        response = HttpResponse(result.getvalue(),content_type='application/pdf')
        filename = "LOCATAIRE_"+str(un_locataire.nom)+' '+str(un_locataire.prenom)+".pdf"
        response['Content-Disposition'] = "attachment; filename="+filename
        return response
        
    return None

####locative
@login_required(login_url='/')
def locative(request):
    etat = 0
    #print(request.user.proprietaire.exist)
    if Proprietaire.objects.filter(user=request.user).exists():
        #liste_locative = Contrat.objects.filter(proprietaire_id=request.user.proprietaire.id).order_by('creation')
        #liste_locative = Contrat.objects.values('locative__reflocative','bien__adresse','bien__ville','bien__quartier','locative__superficie','locative__typelocative','locative__etat','locative__montant','locative__charge','locative__idpub','locative__id').annotate(dcount=Count('locative')).filter(~Q(activecontrat=2),proprietaire_id=Proprietaire.objects.get(user=request.user).id).order_by()
        liste_locative = Locative.objects.filter(etat__gte=1,bien__proprietaire__id=Proprietaire.objects.get(user=request.user).id).order_by('creation')
        etat = 2
    elif Locataire.objects.filter(user=request.user).exists():
        liste_locative = Contrat.objects.values('locative__reflocative','bien__adresse','bien__ville','bien__quartier','locative__superficie','locative__typelocative','locative__etat','locative__montant','locative__charge','locative__idpub','locative__id').annotate(dcount=Count('locative')).filter(~Q(activecontrat=2),locataire_id=Locataire.objects.get(user=request.user).id).order_by()
        etat = 1
    else:
        liste_locative = Locative.objects.filter(etat__gte=1).order_by('creation')
    #liste_locative = Locative.objects.filter(etat__gte=1).order_by('creation')
    content = {
        'etat':etat,
        'locative': True,
        'liste_locative':liste_locative
    }
    return render(request,'gimmo/pages/locative/locative.html',content)

@login_required(login_url='/')
def newlocative(request):
    etat = 0
    liste_bien = Bien.objects.all().order_by('creation')

    content = {
        'etat':etat,
        'locative': True,
        'liste_bien':liste_bien
    }
    return render(request,'gimmo/pages/locative/newlocative.html',content)

@login_required(login_url='/')
def elocative(request,pk):
    etat = 0
    une_locative = get_object_or_404(Locative, idpub=pk)
    liste_bien = Bien.objects.all().order_by('creation')

    content = {
        'etat':etat,
        'locative': True,
        'une_locative':une_locative,
        'liste_bien':liste_bien
    }
    return render(request,'gimmo/pages/locative/elocative.html',content)

def eajxlocative(request):
    etat = 0
    
    if request.method == "POST":
        reflocative = request.POST.get('reflocative',False)
        tplocative = request.POST.get('tplocative',False)
        locativem = request.POST.get('locativem',False)
        mttloyer = request.POST.get('mttloyer',False)
        chargeloyer = request.POST.get('chargeloyer',False)
        nbpiece = request.POST.get('nbpiece',False)
        superficie = request.POST.get('superficie',False)
        bienapp = request.POST.get('bienapp',False)
        idpub = request.POST.get('idpub',False)

        une_locative = get_object_or_404(Locative, idpub=idpub)

        if request.FILES.get('profile', False):
            im1 = request.FILES['profile']
            profile = FileSystemStorage()
            profile = profile.save(im1.name, im1)
        else:
            profile = une_locative.photo
        
        Locative.objects.filter(idpub=idpub).update(
            typelocative = tplocative,
            meuble = locativem,
            montant = mttloyer,
            charge = chargeloyer,
            nombrepiece = nbpiece,
            reflocative = reflocative,
            superficie = superficie,
            photo = profile,
            bien = Bien.objects.get(id=int(bienapp)),
        )
        etat = 1
    
    data = {
        'etat': etat
    }
    return JsonResponse(data)

def ajxlocative(request):
    etat = 0
    
    if request.method == "POST":
        reflocative = request.POST.get('reflocative',False)
        tplocative = request.POST.get('tplocative',False)
        locativem = request.POST.get('locativem',False)
        mttloyer = request.POST.get('mttloyer',False)
        chargeloyer = request.POST.get('chargeloyer',False)
        nbpiece = request.POST.get('nbpiece',False)
        superficie = request.POST.get('superficie',False)
        bienapp = request.POST.get('bienapp',False)

        if request.FILES.get('profile', False):
            im1 = request.FILES['profile']
            profile = FileSystemStorage()
            profile = profile.save(im1.name, im1)
        else:
            profile = ""
        
        count_tab = Locative.objects.all().count()
        idpub = uuid.uuid4()
        idpub = str(idpub).replace("-","")
        publicid = idpub + str(count_tab)
        
        Locative.objects.create(
            idpub = publicid,
            typelocative = tplocative,
            meuble = locativem,
            montant = mttloyer,
            charge = chargeloyer,
            nombrepiece = nbpiece,
            reflocative = reflocative,
            superficie = superficie,
            etat = 1,
            photo = profile,
            bien = Bien.objects.get(id=int(bienapp)),
            creation = datetime.now()
        ).save()
        etat = 1
    
    data = {
        'etat': etat
    }
    return JsonResponse(data)

def infoLocative(request):
    if request.method == 'GET':
        id = request.GET.get('id',False)
        une_locative = get_object_or_404(Locative, idpub=id)
        if une_locative.meuble == 1:
            meuble = 'Oui'
        else:
            meuble = 'Non'
        
        if une_locative.typelocative == 1:
            typelocative = "Palier"
        elif une_locative.typelocative == 2:
            typelocative = "Villa"
        elif une_locative.typelocative == 3:
            typelocative = "Magasin"
        elif une_locative.typelocative == 4:
            typelocative = "Appartement"
        elif une_locative.typelocative == 5:
            typelocative = "Studio"
        else:
            typelocative = "Autre"

        html_data = """
            <div class="row-view">
                <div class="lg-c12 md-c12 sm-c12 xs-c12">
                    <div class="list-btn">
                        <a href="/pdfunelocative/"""+str(id)+"""" class="a-button" style="--clr:#e91919;">
                           <span class="material-icons-sharp">
                            text_snippet
                            </span>
                            Exporter Pdf
                        </a>
                    </div>
                </div>
            </div><br>
            <div class="row-view">
                <div class="lg-c4 md-c4 sm-c3 xs-c6">
                    <div class="info-text">
                        <span class="title-text">Référence</span>
                        <span class="title-content">"""+str(une_locative.reflocative)+"""</span>
                    </div>
                </div>
                <div class="lg-c4 md-c4 sm-c3 xs-c6">
                    <div class="info-text">
                        <span class="title-text">Propriétaire</span>
                        <span class="title-content civilite">"""+str(une_locative.bien.proprietaire.nom.upper())+' '+str(une_locative.bien.proprietaire.prenom)+"""</span>
                    </div>
                </div>
                <div class="lg-c4 md-c4 sm-c3 xs-c6">
                    <div class="info-text">
                        <span class="title-text">Bien</span>
                        <span class="title-content civilite">"""+str(une_locative.bien.nom)+"""</span>
                    </div>
                </div>
                <div class="lg-c4 md-c4 sm-c3 xs-c6">
                    <div class="info-text">
                        <span class="title-text">Type locative</span>
                        <span class="title-content">"""+str(typelocative)+"""</span>
                    </div>
                </div>
                <div class="lg-c4 md-c4 sm-c3 xs-c6">
                    <div class="info-text">
                        <span class="title-text">Locative meublée</span>
                        <span class="title-content">"""+str(meuble)+"""</span>
                    </div>
                </div>
                <div class="lg-c4 md-c4 sm-c3 xs-c6">
                    <div class="info-text">
                        <span class="title-text">Montant loyer</span>
                        <span class="title-content">"""+str(une_locative.montant)+"""</span>
                    </div>
                </div>
                <div class="lg-c4 md-c4 sm-c3 xs-c6">
                    <div class="info-text">
                        <span class="title-text">Charge sur loyer</span>
                        <span class="title-content">"""+str(une_locative.charge)+"""</span>
                    </div>
                </div>
                <div class="lg-c4 md-c4 sm-c3 xs-c6">
                    <div class="info-text">
                        <span class="title-text">Nombre de pièce</span>
                        <span class="title-content">"""+str(une_locative.nombrepiece)+"""</span>
                    </div>
                </div>
                <div class="lg-c4 md-c4 sm-c3 xs-c6">
                    <div class="info-text">
                        <span class="title-text">Superficie (m2)</span>
                        <span class="title-content">"""+str(une_locative.superficie)+"""</span>
                    </div>
                </div>
                
                
            </div>
        """
    data = {
        'une_locative':html_data
    }
    return JsonResponse(data)

def desLocative(request):
    if request.method == 'GET':
        id = request.GET.get('id',False)
        une_locative = get_object_or_404(Locative, idpub=id)
        info_locative = une_locative.reflocative
        
        text = "Confirmer la suppression de la locative <b>"""+info_locative+"</b>"

    data = {
        'text': text
    }
    return JsonResponse(data)

def delLocative(request):
    etat = 0
    if request.method == 'POST':
        id = request.POST.get('dellocativ',False)
        print(id)
        une_locative = get_object_or_404(Locative, idpub=id)
        if une_locative.etat == 2:
            etat = 0
        elif une_locative.etat == 3:
            etat = 2
        else:
            Locative.objects.filter(idpub=id).update(
                etat = 0
            )
            etat = 1
    data = {
        'etat': etat
    }
    return JsonResponse(data)

def pdflocative(request):
    liste_locative = Locative.objects.filter(etat__gte=1).order_by('creation')
    contentdata = {
        'etablissement': Etablissement.objects.get(id=Etablissement.objects.last().id),
        "date": datetime.now(),
        'filenom':"LISTE_LOCATIVE_"+str(datetime.now()),
        'today': datetime.now(),
        'action': request.user.username,
        'liste_locative' : liste_locative
    }
        
    template = get_template('gimmo/pages/locative/pdf-file.html')
    html = template.render(contentdata)

    result = BytesIO()
    pdf = pisa.pisaDocument(BytesIO(html.encode("utf-8")),result)
    if not pdf.err:
        response = HttpResponse(result.getvalue(),content_type='application/pdf')
        filename = "LISTE_LOCATIVE_"+str(datetime.now())+".pdf"
        response['Content-Disposition'] = "attachment; filename="+filename
        return response
        
    return None

def pdfunelocative(request,pk):
    une_locative = Locative.objects.get(idpub=pk)
    contentdata = {
        'etablissement': Etablissement.objects.get(id=Etablissement.objects.last().id),
        "date": datetime.now(),
        'filenom':"LOCATIVE_"+str(une_locative.reflocative),
        'today': datetime.now(),
        'action': request.user.username,
        'une_locative' : une_locative
    }
        
    template = get_template('gimmo/pages/locative/pdf-info.html')
    html = template.render(contentdata)

    result = BytesIO()
    pdf = pisa.pisaDocument(BytesIO(html.encode("utf-8")),result)
    if not pdf.err:
        response = HttpResponse(result.getvalue(),content_type='application/pdf')
        filename = "LOCATIVE_"+str(une_locative.reflocative)+".pdf"
        response['Content-Disposition'] = "attachment; filename="+filename
        return response
        
    return None

####bien
@login_required(login_url='/')
def bien(request):
    etat = 0
    if Proprietaire.objects.filter(user=request.user).exists():
        liste_bien = Bien.objects.filter(proprietaire_id=request.user.proprietaire.id).order_by('creation')
    else:
        liste_bien = Bien.objects.all().order_by('creation')

    content = {
        'etat':etat,
        'bien': True,
        'liste_bien':liste_bien
    }
    return render(request,'gimmo/pages/bien/bien.html',content)

@login_required(login_url='/')
def newbien(request):
    etat = 0
    liste_proprietaire = Proprietaire.objects.filter(d1__gte=1).order_by('creation')

    content = {
        'etat':etat,
        'bien': True,
        'liste_proprietaire':liste_proprietaire
    }
    return render(request,'gimmo/pages/bien/newbien.html',content)


@login_required(login_url='/')
def ebien(request,pk):
    etat = 0
    un_bien = get_object_or_404(Bien, idpub=pk)
    liste_proprietaire = Proprietaire.objects.filter(d1__gte=1).order_by('creation')

    content = {
        'etat':etat,
        'bien': True,
        'un_bien':un_bien,
        'liste_proprietaire':liste_proprietaire
    }
    return render(request,'gimmo/pages/bien/ebien.html',content)

def eajxbien(request):
    etat = 0
    
    if request.method == "POST":
        vente = request.POST.get('vente',False)
        numlot = request.POST.get('numlot',False)
        lot = request.POST.get('lot',False)
        titrefoncier = request.POST.get('titrefoncier',False)
        superficie = request.POST.get('superficie',False)
        nombien = request.POST.get('nombien',False)
        typebien = request.POST.get('typebien',False)
        adresse = request.POST.get('adresse',False)
        ville = request.POST.get('ville',False)
        quartier = request.POST.get('quartier',False)
        valeur = request.POST.get('valeur',False)
        commission = 0
        proprietaire = request.POST.get('proprietaire',False)
        idpub = request.POST.get('idpub',False)

        un_bien = get_object_or_404(Bien, idpub=idpub)

        if request.FILES.get('profile', False):
            im1 = request.FILES['profile']
            profile = FileSystemStorage()
            profile = profile.save(im1.name, im1)
        else:
            profile = un_bien.photo
        
        Bien.objects.filter(idpub=idpub).update(
            vente = vente,
            numlot = numlot,
            lot = lot,
            titrefoncier = titrefoncier,
            superficie = superficie,
            nom = nombien,
            typebien = typebien,
            adresse = adresse,
            ville = ville,
            quartier = quartier,
            valeur = valeur,
            commision = commission,
            etat = 1,
            mandat = '',
            photo = profile,
            proprietaire = Proprietaire.objects.get(id=int(proprietaire))
        )
        etat = 1
    
    data = {
        'etat': etat
    }
    return JsonResponse(data)

def ajxbien(request):
    etat = 0
    
    if request.method == "POST":
        vente = request.POST.get('vente',False)
        numlot = request.POST.get('numlot',False)
        lot = request.POST.get('lot',False)
        titrefoncier = request.POST.get('titrefoncier',False)
        superficie = request.POST.get('superficie',False)
        nombien = request.POST.get('nombien',False)
        typebien = request.POST.get('typebien',False)
        adresse = request.POST.get('adresse',False)
        ville = request.POST.get('ville',False)
        quartier = request.POST.get('quartier',False)
        valeur = request.POST.get('valeur',False)
        commission = 0
        proprietaire = request.POST.get('proprietaire',False)

        if request.FILES.get('profile', False):
            im1 = request.FILES['profile']
            profile = FileSystemStorage()
            profile = profile.save(im1.name, im1)
        else:
            profile = ""
        
        count_tab = Bien.objects.all().count()
        idpub = uuid.uuid4()
        idpub = str(idpub).replace("-","")
        publicid = idpub + str(count_tab)
        
        Bien.objects.create(
            idpub = publicid,
            vente = vente,
            numlot = numlot,
            lot = lot,
            titrefoncier = titrefoncier,
            superficie = superficie,
            nom = nombien,
            typebien = typebien,
            adresse = adresse,
            ville = ville,
            quartier = quartier,
            valeur = valeur,
            commision = commission,
            etat = 1,
            mandat = '',
            photo = profile,
            proprietaire = Proprietaire.objects.get(id=int(proprietaire)),
            creation = datetime.now()
        ).save()
        etat = 1
    
    data = {
        'etat': etat
    }
    return JsonResponse(data)

def infoBien(request):
    if request.method == 'GET':
        id = request.GET.get('id',False)
        un_bien = get_object_or_404(Bien, idpub=id)
        if un_bien.vente == 1:
            vente = 'En vente'
        else:
            vente = 'En location'
        
        if un_bien.typebien == 1:
            typebien = "Immeuble"
        elif un_bien.typebien == 2:
            typebien = "Maison basse"
        elif un_bien.typebien == 3:
            typebien = "Duplex"
        elif un_bien.typebien == 4:
            typebien = "Villa"
        elif un_bien.typebien == 5:
            typebien = "Appartement"
        elif un_bien.typebien == 6:
            typebien = "Terrain"
        else:
            typebien = "Autre"

        html_data = """
            <div class="row-view">
                <div class="lg-c12 md-c12 sm-c12 xs-c12">
                    <div class="list-btn">
                        <a href="/pdfunbien/"""+str(id)+"""" class="a-button" style="--clr:#e91919;">
                           <span class="material-icons-sharp">
                            text_snippet
                            </span>
                            Exporter Pdf
                        </a>
                    </div>
                </div>
            </div><br>
            <div class="row-view">
                <div class="lg-c4 md-c4 sm-c3 xs-c6">
                    <div class="info-text">
                        <span class="title-text">Référence</span>
                        <span class="title-content">"""+str(un_bien.nom)+"""</span>
                    </div>
                </div>
                <div class="lg-c4 md-c4 sm-c3 xs-c6">
                    <div class="info-text">
                        <span class="title-text">Propriétaire</span>
                        <span class="title-content civilite">"""+str(un_bien.proprietaire.nom.upper())+' '+str(un_bien.proprietaire.prenom)+"""</span>
                    </div>
                </div>
                <div class="lg-c4 md-c4 sm-c3 xs-c6">
                    <div class="info-text">
                        <span class="title-text">N° lot</span>
                        <span class="title-content civilite">"""+str(un_bien.numlot)+"""</span>
                    </div>
                </div>
                <div class="lg-c4 md-c4 sm-c3 xs-c6">
                    <div class="info-text">
                        <span class="title-text">Lot</span>
                        <span class="title-content">"""+str(un_bien.lot)+"""</span>
                    </div>
                </div>
                <div class="lg-c4 md-c4 sm-c3 xs-c6">
                    <div class="info-text">
                        <span class="title-text">Titre foncier</span>
                        <span class="title-content">"""+str(un_bien.titrefoncier)+"""</span>
                    </div>
                </div>
                <div class="lg-c4 md-c4 sm-c3 xs-c6">
                    <div class="info-text">
                        <span class="title-text">Type de bien</span>
                        <span class="title-content">"""+str(typebien)+"""</span>
                    </div>
                </div>
                <div class="lg-c4 md-c4 sm-c3 xs-c6">
                    <div class="info-text">
                        <span class="title-text">Superficie (m2)</span>
                        <span class="title-content">"""+str(un_bien.superficie)+"""</span>
                    </div>
                </div>
                <div class="lg-c4 md-c4 sm-c3 xs-c6">
                    <div class="info-text">
                        <span class="title-text">Adresse</span>
                        <span class="title-content">"""+str(un_bien.adresse)+"""</span>
                    </div>
                </div>
                <div class="lg-c4 md-c4 sm-c3 xs-c6">
                    <div class="info-text">
                        <span class="title-text">Ville</span>
                        <span class="title-content">"""+str(un_bien.ville)+"""</span>
                    </div>
                </div>
                <div class="lg-c4 md-c4 sm-c3 xs-c6">
                    <div class="info-text">
                        <span class="title-text">Quartier</span>
                        <span class="title-content">"""+str(un_bien.quartier)+"""</span>
                    </div>
                </div>
                <div class="lg-c4 md-c4 sm-c3 xs-c6">
                    <div class="info-text">
                        <span class="title-text">Valeur</span>
                        <span class="title-content">"""+str(un_bien.valeur)+"""</span>
                    </div>
                </div>
                <div class="lg-c4 md-c4 sm-c3 xs-c6">
                    <div class="info-text">
                        <span class="title-text">Date création</span>
                        <span class="title-content">"""+str(un_bien.creation)+"""</span>
                    </div>
                </div>
                
                
            </div>
        """
    data = {
        'un_bien':html_data
    }
    return JsonResponse(data)

def desBien(request):
    if request.method == 'GET':
        id = request.GET.get('id',False)
        une_locative = get_object_or_404(locative, idpub=id)
        info_locative = une_locative.reflocative
        
        text = "Confirmer la suppression de la locative <b>"""+info_locative+"</b>"
        
    data = {
        'text': text
    }
    return JsonResponse(data)

def delBien(request):
    etat = 0
    if request.method == 'GET':
        id = request.GET.get('dellocative',False)
        une_locative = get_object_or_404(locative, idpub=id)
        if Contrat.objects.filter(locative_id=une_locative.id).exists():
            etat = 0
        else:
            Locative.objects.filter(idpub=id).update(
                etat = 0
            )
            etat = 1
    data = {
        'etat': etat
    }
    return JsonResponse(data)

def pdfbien(request):
    if Proprietaire.objects.filter(user=request.user).exists():
        liste_bien = Bien.objects.filter(proprietaire_id=request.user.proprietaire.id).order_by('creation')
    else:
        liste_bien = Bien.objects.all().order_by('creation')
    contentdata = {
        'etablissement': Etablissement.objects.get(id=Etablissement.objects.last().id),
        "date": datetime.now(),
        'filenom':"LISTE_BIEN_"+str(datetime.now()),
        'today': datetime.now(),
        'action': request.user.username,
        'liste_bien' : liste_bien
    }
        
    template = get_template('gimmo/pages/bien/pdf-file.html')
    html = template.render(contentdata)

    result = BytesIO()
    pdf = pisa.pisaDocument(BytesIO(html.encode("utf-8")),result)
    if not pdf.err:
        response = HttpResponse(result.getvalue(),content_type='application/pdf')
        filename = "LISTE_BIEN_"+str(datetime.now())+".pdf"
        response['Content-Disposition'] = "attachment; filename="+filename
        return response
        
    return None

def pdfunbien(request,pk):
    un_bien = Bien.objects.get(idpub=pk)
    contentdata = {
        'etablissement': Etablissement.objects.get(id=Etablissement.objects.last().id),
        "date": datetime.now(),
        'filenom':"BIEN_"+str(un_bien.nom),
        'today': datetime.now(),
        'action': request.user.username,
        'un_bien' : un_bien
    }
        
    template = get_template('gimmo/pages/bien/pdf-info.html')
    html = template.render(contentdata)

    result = BytesIO()
    pdf = pisa.pisaDocument(BytesIO(html.encode("utf-8")),result)
    if not pdf.err:
        response = HttpResponse(result.getvalue(),content_type='application/pdf')
        filename = "BIEN_"+str(un_bien.nom)+".pdf"
        response['Content-Disposition'] = "attachment; filename="+filename
        return response
        
    return None


####contrat
@login_required(login_url='/')
def contrat(request):
    etat = 0
    if Proprietaire.objects.filter(user=request.user).exists():
        liste_contrat = Contrat.objects.filter(proprietaire_id=request.user.proprietaire.id).order_by('creation')
    elif Locataire.objects.filter(user=request.user).exists():
        liste_contrat = Contrat.objects.filter(locataire_id=request.user.locataire.id).order_by('creation')
    else:
        liste_contrat = Contrat.objects.all().order_by('creation')

    content = {
        'etat':etat,
        'contrat': True,
        'liste_contrat':liste_contrat
    }
    return render(request,'gimmo/pages/contrat/contrat.html',content)

@login_required(login_url='/')
def newcontrat(request):
    etat = 0
    un_etablissement = Etablissement.objects.get(id=Etablissement.objects.last().id)

    content = {
        'etat':etat,
        'contrat': True,
        'liste_proprietaire': Proprietaire.objects.filter(d1__gte=1).order_by('nom'),
        'liste_locataire': Locataire.objects.filter(d1__gte=1).order_by('nom'),
        'un_etablissement':un_etablissement
    }
    return render(request,'gimmo/pages/contrat/newcontrat.html',content)


@login_required(login_url='/')
def econtrat(request,pk):
    etat = 0
    un_etablissement = Etablissement.objects.get(id=Etablissement.objects.last().id)
    un_contrat = get_object_or_404(Contrat, idpub=pk)
    une_facture = get_object_or_404(Facture, contrat_id=un_contrat.id)

    if str(un_contrat.datesign) == '2021-12-14':
        dates = ''
    else:
        dates = datetime.strptime(str(un_contrat.datesign), '%Y-%m-%d').strftime('%Y-%m-%d')
    
    if str(un_contrat.dateentree) == '2021-12-14':
        datee = ''
    else:
        datee = datetime.strptime(str(un_contrat.dateentree), '%Y-%m-%d').strftime('%Y-%m-%d')

    if str(un_contrat.datefin) == '2021-12-14' or str(un_contrat.datefin) == '' or str(un_contrat.datefin) == 'None':
        datef = ''
    else:
        datef = datetime.strptime(str(un_contrat.datefin), '%Y-%m-%d').strftime('%Y-%m-%d')

    content = {
        'etat':etat,
        'contrat': True,
        'liste_proprietaire': Proprietaire.objects.filter(d1__gte=1).order_by('nom'),
        'liste_locataire': Locataire.objects.filter(d1__gte=1).order_by('nom'),
        'un_contrat':un_contrat,
        'une_facture':une_facture,
        'dates':dates,
        'datee':datee,
        'datef':datef,
        'un_etablissement':un_etablissement
    }
    return render(request,'gimmo/pages/contrat/econtrat.html',content)


def ajxcontrat(request):
    etat = 0
    
    if request.method == "POST":
        proprietaire = request.POST.get('proprietaire',False)
        bien = request.POST.get('bien',False)
        locative = request.POST.get('locative',False)
        locataire = request.POST.get('locataire',False)
        typecontrat = request.POST.get('typecontrat',False)
        caution = request.POST.get('caution',False)
        avance = request.POST.get('avance',False)
        datesign = request.POST.get('datesign',False)
        dateentree = request.POST.get('dateentree',False)
        datefin = request.POST.get('datefin',False)
        retard = request.POST.get('retard',False)
        limite = request.POST.get('limite',False)
        visitemtt = request.POST.get('visitemtt',False)
        visiteqte = request.POST.get('visiteqte',False)
        visitetva = request.POST.get('visitetva',False)
        visitetot = request.POST.get('visitetot',False)
        honorairemtt = request.POST.get('honorairemtt',False)
        honoraireqte = request.POST.get('honoraireqte',False)
        honorairetva = request.POST.get('honorairetva',False)
        honorairetot = request.POST.get('honorairetot',False)
        droitmtt = request.POST.get('droitmtt',False)
        droitqte = request.POST.get('droitqte',False)
        droittva = request.POST.get('droittva',False)
        droittot = request.POST.get('droittot',False)
        timbremtt = request.POST.get('timbremtt',False)
        timbreqte = request.POST.get('timbreqte',False)
        timbretva = request.POST.get('timbretva',False)
        timbretot = request.POST.get('timbretot',False)
        fraisdossiermtt = request.POST.get('fraisdossiermtt',False)
        fraisdossierqte = request.POST.get('fraisdossierqte',False)
        fraisdossiertva = request.POST.get('fraisdossiertva',False)
        fraisdossiertot = request.POST.get('fraisdossiertot',False)
        assurancemtt = request.POST.get('assurancemtt',False)
        assuranceqte = request.POST.get('assuranceqte',False)
        assurancetva = request.POST.get('assurancetva',False)
        assurancetot = request.POST.get('assurancetot',False)
        activecontrat = request.POST.get('activecontrat',False)
        nbpaiement = request.POST.get('nbpaiement',False)

        if activecontrat == False or activecontrat == '':
            activecontrat = 0
            etat_locative = 3
        else:
            activecontrat = 1
            etat_locative = 2
            del_unsed_contrat = Contrat.objects.filter(locative_id=int(locative))
            for un_contrat in del_unsed_contrat:
                if un_contrat.activecontrat == 0:
                    Contrat.objects.filter(id=un_contrat.id).delete()
        
        print(datefin)

        if datefin == '' or datefin == False:
            datefin = None
        else:
            datefin = datefin
        
        count_tab = Contrat.objects.all().count()
        idpub = uuid.uuid4()
        idpub = str(idpub).replace("-","")
        publicid = idpub + str(count_tab)

        ref_contrat = 'CT26-'+str(count_tab)

        montant_locative = Locative.objects.get(id=int(locative)).montant
        totcaution = int(caution)*float(montant_locative)
        totavance = int(avance)*float(montant_locative)
        totallocative = totcaution+totavance
        totalsurlocative = float(visitemtt)+float(honorairemtt)+float(droitmtt)+float(timbremtt)+float(fraisdossiermtt)+float(assurancemtt)
        totalgeneral = totalsurlocative+totallocative


        #PROCHAIN PAIEMENT
        mois_apres_pay = int(nbpaiement)
        start_date = str(dateentree)+' 00:00:01'
        date_format_str = '%Y-%m-%d %H:%M:%S'
        start = datetime.strptime(start_date, date_format_str)
        date_1 = pd.to_datetime(start)
        end_date = date_1+pd.DateOffset(months=mois_apres_pay,days=int(limite))
        
        Contrat.objects.create(
            idpub = publicid,
            refcontrat = ref_contrat,
            typecontrat = typecontrat,
            caution = caution,
            totcaution = totcaution,
            avance = avance,
            totavance = totavance,
            totallocative = totallocative,
            totalsurlocative = totalsurlocative,
            totalgeneral = totalgeneral,
            nbpaiement = nbpaiement,
            prochainpay = end_date,
            datesign = datesign,
            dateentree = dateentree,
            datefin = datefin,
            retard = retard,
            limite = int(limite),
            visitemtt = visitemtt,
            visiteqte = visiteqte,
            visitetva = visitetva,
            visitetot = visitetot,
            honorairemtt = honorairemtt,
            honoraireqte = honoraireqte,
            honorairetva = honorairetva,
            honorairetot = honorairetot,
            droitmtt = droitmtt,
            droitqte = droitqte,
            droittva = droittva,
            droittot = droittot,
            timbremtt = timbremtt,
            timbreqte = timbreqte,
            timbretva = timbretva,
            timbretot = timbretot,
            fraisdossiermtt = fraisdossiermtt,
            fraisdossierqte = fraisdossierqte,
            fraisdossiertva = fraisdossiertva,
            fraisdossiertot = fraisdossiertot,
            assurancemtt = assurancemtt,
            assuranceqte = assuranceqte,
            assurancetva = assurancetva,
            assurancetot = assurancetot,
            activecontrat = activecontrat,
            proprietaire = Proprietaire.objects.get(id=int(proprietaire)),
            bien = Bien.objects.get(id=int(bien)),
            locative = Locative.objects.get(id=int(locative)),
            locataire = Locataire.objects.get(id=int(locataire)),
            creation = datetime.now()
        ).save()

        Locative.objects.filter(id=int(locative)).update(
            etat = int(etat_locative)
        )

        count_tab_facture = Facture.objects.all().count()
        idpub_facture = uuid.uuid4()
        idpub_facture = str(idpub_facture).replace("-","")
        publicid_facture = idpub_facture + str(count_tab_facture)
        ref_facture = 'FT26-'+str(count_tab_facture)

        Facture.objects.create(
            idpub = publicid_facture,
            reffacture = ref_facture,
            typefacture = 'Avance/Caution',
            dureepay = 1,
            debutpay = None,
            finpay = None,
            totfacture = totalgeneral,
            payefacture = 0,
            restefacture = totalgeneral,
            retardfacture = 0,
            finaltotal = totalgeneral,
            etat = 3,
            locataire = Locataire.objects.get(id=int(locataire)),
            locative = Locative.objects.get(id=int(locative)),
            contrat = Contrat.objects.get(refcontrat=ref_contrat),
            creation = datetime.now()
        ).save()
        etat = 1
    
    data = {
        'etat': etat
    }
    return JsonResponse(data)

def eajxcontrat(request):
    etat = 0
    
    if request.method == "POST":
        proprietaire = request.POST.get('proprietaire',False)
        bien = request.POST.get('bien',False)
        locative = request.POST.get('locative',False)
        locataire = request.POST.get('locataire',False)
        typecontrat = request.POST.get('typecontrat',False)
        caution = request.POST.get('caution',False)
        avance = request.POST.get('avance',False)
        datesign = request.POST.get('datesign',False)
        dateentree = request.POST.get('dateentree',False)
        datefin = request.POST.get('datefin',False)
        retard = request.POST.get('retard',False)
        limite = request.POST.get('limite',False)
        visitemtt = request.POST.get('visitemtt',False)
        visiteqte = request.POST.get('visiteqte',False)
        visitetva = request.POST.get('visitetva',False)
        visitetot = request.POST.get('visitetot',False)
        honorairemtt = request.POST.get('honorairemtt',False)
        honoraireqte = request.POST.get('honoraireqte',False)
        honorairetva = request.POST.get('honorairetva',False)
        honorairetot = request.POST.get('honorairetot',False)
        droitmtt = request.POST.get('droitmtt',False)
        droitqte = request.POST.get('droitqte',False)
        droittva = request.POST.get('droittva',False)
        droittot = request.POST.get('droittot',False)
        timbremtt = request.POST.get('timbremtt',False)
        timbreqte = request.POST.get('timbreqte',False)
        timbretva = request.POST.get('timbretva',False)
        timbretot = request.POST.get('timbretot',False)
        fraisdossiermtt = request.POST.get('fraisdossiermtt',False)
        fraisdossierqte = request.POST.get('fraisdossierqte',False)
        fraisdossiertva = request.POST.get('fraisdossiertva',False)
        fraisdossiertot = request.POST.get('fraisdossiertot',False)
        assurancemtt = request.POST.get('assurancemtt',False)
        assuranceqte = request.POST.get('assuranceqte',False)
        assurancetva = request.POST.get('assurancetva',False)
        assurancetot = request.POST.get('assurancetot',False)
        activecontrat = request.POST.get('activecontrat',False)
        idpub = request.POST.get('idpub',False)
        nbpaiement = request.POST.get('nbpaiement',False)

        if activecontrat == False or activecontrat == '':
            activecontrat = 0
            etat_locative = 3
        else:
            activecontrat = 1
            etat_locative = 2

            del_unsed_contrat = Contrat.objects.filter(locative_id=int(locative))
            for un_contrat in del_unsed_contrat:
                if un_contrat.activecontrat == 0 and un_contrat.idpub != idpub:
                    Contrat.objects.filter(id=un_contrat.id).delete()

        if datefin == '' or datefin == False:
            datefin = None
        else:
            datefin = datefin
        
        #PROCHAIN PAIEMENT
        mois_apres_pay = int(nbpaiement)
        start_date = str(dateentree)+' 00:00:01'
        date_format_str = '%Y-%m-%d %H:%M:%S'
        start = datetime.strptime(start_date, date_format_str)
        date_1 = pd.to_datetime(start)
        end_date = date_1+pd.DateOffset(months=mois_apres_pay,days=int(limite))
        
        
        
        montant_locative = Locative.objects.get(id=int(locative)).montant
        totcaution = float(caution)*float(montant_locative)
        totavance = float(avance)*float(montant_locative)
        totallocative = totcaution+totavance
        totalsurlocative = float(visitemtt)+float(honorairemtt)+float(droitmtt)+float(timbremtt)+float(fraisdossiermtt)+float(assurancemtt)
        totalgeneral = totalsurlocative+totallocative
        
        un_contrat = Contrat.objects.get(idpub=idpub)
        Locative.objects.filter(id=un_contrat.locative.id).update(
            etat = 1
        )

        Contrat.objects.filter(idpub=idpub).update(
            typecontrat = typecontrat,
            caution = caution,
            totcaution = totcaution,
            avance = avance,
            totavance = totavance,
            totallocative = totallocative,
            totalsurlocative = totalsurlocative,
            totalgeneral = totalgeneral,
            nbpaiement = nbpaiement,
            prochainpay = end_date,
            datesign = datesign,
            dateentree = dateentree,
            datefin = datefin,
            retard = retard,
            limite = limite,
            visitemtt = visitemtt,
            visiteqte = visiteqte,
            visitetva = visitetva,
            visitetot = visitetot,
            honorairemtt = honorairemtt,
            honoraireqte = honoraireqte,
            honorairetva = honorairetva,
            honorairetot = honorairetot,
            droitmtt = droitmtt,
            droitqte = droitqte,
            droittva = droittva,
            droittot = droittot,
            timbremtt = timbremtt,
            timbreqte = timbreqte,
            timbretva = timbretva,
            timbretot = timbretot,
            fraisdossiermtt = fraisdossiermtt,
            fraisdossierqte = fraisdossierqte,
            fraisdossiertva = fraisdossiertva,
            fraisdossiertot = fraisdossiertot,
            assurancemtt = assurancemtt,
            assuranceqte = assuranceqte,
            assurancetva = assurancetva,
            assurancetot = assurancetot,
            activecontrat = activecontrat,
            proprietaire = Proprietaire.objects.get(id=int(proprietaire)),
            bien = Bien.objects.get(id=int(bien)),
            locative = Locative.objects.get(id=int(locative)),
            locataire = Locataire.objects.get(id=int(locataire))
        )
        restfacture = (totalgeneral - Facture.objects.get(contrat_id=Contrat.objects.get(idpub=idpub).id).payefacture)
        if restfacture <= 0:
            etat_facture = 1
        elif restfacture > 0 and restfacture < totalgeneral:
            etat_facture = 4
        else:
            etat_facture = 3

        Facture.objects.filter(contrat_id=Contrat.objects.get(idpub=idpub).id).update(
            totfacture = totalgeneral,
            restefacture = restfacture,
            retardfacture = 0,
            finaltotal = totalgeneral,
            etat = etat_facture,
            locataire = Locataire.objects.get(id=int(locataire)),
            locative = Locative.objects.get(id=int(locative))
        )

        Locative.objects.filter(id=int(locative)).update(
            etat = int(etat_locative)
        )
        etat = 1
    
    data = {
        'etat': etat
    }
    return JsonResponse(data)

def bienproprietaire(request):
    if request.method == 'GET':
        id = request.GET.get('id',False)
        listebien = Bien.objects.filter(proprietaire=int(id),etat=1).values('id','nom').order_by("nom")
        
    data = {
        'listebien': list(listebien)
    }
    return JsonResponse(data)

def locativeproprietaire(request):
    if request.method == 'GET':
        id = request.GET.get('id',False)
        listelocative = Locative.objects.filter(bien=int(id),etat__gte=1).values('id','reflocative','etat').order_by("reflocative")
        
    data = {
        'listelocative': list(listelocative)
    }
    return JsonResponse(data)

def selectedlocative(request):
    if request.method == 'GET':
        id = request.GET.get('id',False)
        montant = Locative.objects.get(id=int(id)).montant
        
    data = {
        'montant': montant
    }
    return JsonResponse(data)


def infoContrat(request):
    if request.method == 'GET':
        id = request.GET.get('id',False)
        un_contrat = get_object_or_404(Contrat, idpub=id)

        if un_contrat.typecontrat == 1:
            typecontrat = 'Contrat de bail habitation'
        else:
            typecontrat = 'Contrat de bail commercial'
        

        if un_contrat.activecontrat == 1:
            etatcontrat = 'Actif'
        elif un_contrat.activecontrat == 2:
            etatcontrat = 'Terminé'
        else:
            etatcontrat = 'En attente'

        html_data = """
            <div class="row-view">
                <div class="lg-c12 md-c12 sm-c12 xs-c12">
                    <div class="list-btn">
                        <a href="/pdfuncontrat/"""+str(id)+"""" class="a-button" style="--clr:#e91919;">
                           <span class="material-icons-sharp">
                            text_snippet
                            </span>
                            Exporter Pdf
                        </a>
                    </div>
                </div>
            </div><br>
            <div class="row-view">
                <div class="lg-c4 md-c4 sm-c3 xs-c6">
                    <div class="info-text">
                        <span class="title-text">Locataire</span>
                        <span class="title-content">"""+str(un_contrat.locataire.nom.upper())+' '+str(un_contrat.locataire.prenom)+"""</span>
                    </div>
                </div>
                <div class="lg-c4 md-c4 sm-c3 xs-c6">
                    <div class="info-text">
                        <span class="title-text">Propriétaire</span>
                        <span class="title-content civilite">"""+str(un_contrat.proprietaire.nom.upper())+' '+str(un_contrat.proprietaire.prenom)+"""</span>
                    </div>
                </div>
                <div class="lg-c4 md-c4 sm-c3 xs-c6">
                    <div class="info-text">
                        <span class="title-text">Bien</span>
                        <span class="title-content civilite">"""+str(un_contrat.bien.nom)+"""</span>
                    </div>
                </div>
                <div class="lg-c4 md-c4 sm-c3 xs-c6">
                    <div class="info-text">
                        <span class="title-text">Locative</span>
                        <span class="title-content civilite">"""+str(un_contrat.locative.reflocative)+"""</span>
                    </div>
                </div>
                <div class="lg-c4 md-c4 sm-c3 xs-c6">
                    <div class="info-text">
                        <span class="title-text">Référence contrat</span>
                        <span class="title-content">"""+str(un_contrat.refcontrat)+"""</span>
                    </div>
                </div>
                
                <div class="lg-c4 md-c4 sm-c3 xs-c6">
                    <div class="info-text">
                        <span class="title-text">Type contrat</span>
                        <span class="title-content">"""+str(typecontrat)+"""</span>
                    </div>
                </div>
                <div class="lg-c4 md-c4 sm-c3 xs-c6">
                    <div class="info-text">
                        <span class="title-text">Caution</span>
                        <span class="title-content">"""+str(un_contrat.caution)+"""</span>
                    </div>
                </div>
                
                <div class="lg-c4 md-c4 sm-c3 xs-c6">
                    <div class="info-text">
                        <span class="title-text">Avance</span>
                        <span class="title-content">"""+str(un_contrat.avance)+"""</span>
                    </div>
                </div>

                <div class="lg-c4 md-c4 sm-c3 xs-c6">
                    <div class="info-text">
                        <span class="title-text">Montant total locative</span>
                        <span class="title-content">"""+str(un_contrat.totallocative)+"""</span>
                    </div>
                </div>
                <div class="lg-c4 md-c4 sm-c3 xs-c6">
                    <div class="info-text">
                        <span class="title-text">Frais total sur locative</span>
                        <span class="title-content">"""+str(un_contrat.totalsurlocative)+"""</span>
                    </div>
                </div>
                <div class="lg-c4 md-c4 sm-c3 xs-c6">
                    <div class="info-text">
                        <span class="title-text">Net locative</span>
                        <span class="title-content">"""+str(un_contrat.totalgeneral)+"""</span>
                    </div>
                </div>
                <div class="lg-c4 md-c4 sm-c3 xs-c6">
                    <div class="info-text">
                        <span class="title-text">Date signature</span>
                        <span class="title-content">"""+str(un_contrat.datesign)+"""</span>
                    </div>
                </div>
                <div class="lg-c4 md-c4 sm-c3 xs-c6">
                    <div class="info-text">
                        <span class="title-text">Date début contrat</span>
                        <span class="title-content">"""+str(un_contrat.dateentree)+"""</span>
                    </div>
                </div>
                
                <div class="lg-c4 md-c4 sm-c3 xs-c6">
                    <div class="info-text">
                        <span class="title-text">Date fin contrat</span>
                        <span class="title-content">"""+str(un_contrat.datefin)+"""</span>
                    </div>
                </div>
                
                <div class="lg-c4 md-c4 sm-c3 xs-c6">
                    <div class="info-text">
                        <span class="title-text">Pourcentage à imputer en cas de retard</span>
                        <span class="title-content">"""+str(un_contrat.retard)+"""</span>
                    </div>
                </div>
                <div class="lg-c4 md-c4 sm-c3 xs-c6">
                    <div class="info-text">
                        <span class="title-text">Jour ajouté à la date de paiement</span>
                        <span class="title-content">"""+str(un_contrat.limite)+"""</span>
                    </div>
                </div>

                <div class="lg-c4 md-c4 sm-c3 xs-c6">
                    <div class="info-text">
                        <span class="title-text">Prochain paiement</span>
                        <span class="title-content">"""+str(un_contrat.prochainpay)+"""</span>
                    </div>
                </div>

                <div class="lg-c12 md-c12 sm-c12 xs-c12">
                    <h3 class="cl-primary">Propriétaire & Agence</h3><br>
                </div>
                <div class="lg-c12 md-c12 sm-c12 xs-c12">
                    <h4  class="cl-primary">Visite du site</h4><br>
                </div>

                <div class="lg-c3 md-c3 sm-c6 xs-c12">
                    <div class="info-text">
                        <span class="title-text">Montant</span>
                        <span class="title-content">"""+str(un_contrat.visitemtt)+"""</span>
                    </div>
                </div>
                <div class="lg-c3 md-c3 sm-c6 xs-c12">
                    <div class="info-text">
                        <span class="title-text">Qté</span>
                        <span class="title-content">"""+str(un_contrat.visiteqte)+"""</span>
                    </div>
                </div>
                <div class="lg-c3 md-c3 sm-c6 xs-c12">
                    <div class="info-text">
                        <span class="title-text">TVA</span>
                        <span class="title-content">"""+str(un_contrat.visitetva)+"""</span>
                    </div>
                </div>
                <div class="lg-c3 md-c3 sm-c6 xs-c12">
                    <div class="info-text">
                        <span class="title-text">Total</span>
                        <span class="title-content">"""+str(un_contrat.visitetot)+"""</span>
                    </div>
                </div>

                <div class="lg-c12 md-c12 sm-c12 xs-c12">
                    <h4  class="cl-primary">Honoraire</h4><br>
                </div>

                <div class="lg-c3 md-c3 sm-c6 xs-c12">
                    <div class="info-text">
                        <span class="title-text">Montant</span>
                        <span class="title-content">"""+str(un_contrat.honorairemtt)+"""</span>
                    </div>
                </div>
                <div class="lg-c3 md-c3 sm-c6 xs-c12">
                    <div class="info-text">
                        <span class="title-text">Qté</span>
                        <span class="title-content">"""+str(un_contrat.honoraireqte)+"""</span>
                    </div>
                </div>
                <div class="lg-c3 md-c3 sm-c6 xs-c12">
                    <div class="info-text">
                        <span class="title-text">TVA</span>
                        <span class="title-content">"""+str(un_contrat.honorairetva)+"""</span>
                    </div>
                </div>
                <div class="lg-c3 md-c3 sm-c6 xs-c12">
                    <div class="info-text">
                        <span class="title-text">Total</span>
                        <span class="title-content">"""+str(un_contrat.honorairetot)+"""</span>
                    </div>
                </div>

                <div class="lg-c12 md-c12 sm-c12 xs-c12">
                    <h4  class="cl-primary">Droit d'enrégistrement</h4><br>
                </div>

                <div class="lg-c3 md-c3 sm-c6 xs-c12">
                    <div class="info-text">
                        <span class="title-text">Montant</span>
                        <span class="title-content">"""+str(un_contrat.droitmtt)+"""</span>
                    </div>
                </div>
                <div class="lg-c3 md-c3 sm-c6 xs-c12">
                    <div class="info-text">
                        <span class="title-text">Qté</span>
                        <span class="title-content">"""+str(un_contrat.droitqte)+"""</span>
                    </div>
                </div>
                <div class="lg-c3 md-c3 sm-c6 xs-c12">
                    <div class="info-text">
                        <span class="title-text">TVA</span>
                        <span class="title-content">"""+str(un_contrat.droittva)+"""</span>
                    </div>
                </div>
                <div class="lg-c3 md-c3 sm-c6 xs-c12">
                    <div class="info-text">
                        <span class="title-text">Total</span>
                        <span class="title-content">"""+str(un_contrat.droittot)+"""</span>
                    </div>
                </div>

                <div class="lg-c12 md-c12 sm-c12 xs-c12">
                    <h4  class="cl-primary">Timbres fiscaux + transport</h4><br>
                </div>

                <div class="lg-c3 md-c3 sm-c6 xs-c12">
                    <div class="info-text">
                        <span class="title-text">Montant</span>
                        <span class="title-content">"""+str(un_contrat.timbremtt)+"""</span>
                    </div>
                </div>
                <div class="lg-c3 md-c3 sm-c6 xs-c12">
                    <div class="info-text">
                        <span class="title-text">Qté</span>
                        <span class="title-content">"""+str(un_contrat.timbreqte)+"""</span>
                    </div>
                </div>
                <div class="lg-c3 md-c3 sm-c6 xs-c12">
                    <div class="info-text">
                        <span class="title-text">TVA</span>
                        <span class="title-content">"""+str(un_contrat.timbretva)+"""</span>
                    </div>
                </div>
                <div class="lg-c3 md-c3 sm-c6 xs-c12">
                    <div class="info-text">
                        <span class="title-text">Total</span>
                        <span class="title-content">"""+str(un_contrat.timbretot)+"""</span>
                    </div>
                </div>

                <div class="lg-c12 md-c12 sm-c12 xs-c12">
                    <h4  class="cl-primary">Frais de dossier</h4><br>
                </div>

                <div class="lg-c3 md-c3 sm-c6 xs-c12">
                    <div class="info-text">
                        <span class="title-text">Montant</span>
                        <span class="title-content">"""+str(un_contrat.fraisdossiermtt)+"""</span>
                    </div>
                </div>
                <div class="lg-c3 md-c3 sm-c6 xs-c12">
                    <div class="info-text">
                        <span class="title-text">Qté</span>
                        <span class="title-content">"""+str(un_contrat.fraisdossierqte)+"""</span>
                    </div>
                </div>
                <div class="lg-c3 md-c3 sm-c6 xs-c12">
                    <div class="info-text">
                        <span class="title-text">TVA</span>
                        <span class="title-content">"""+str(un_contrat.fraisdossiertva)+"""</span>
                    </div>
                </div>
                <div class="lg-c3 md-c3 sm-c6 xs-c12">
                    <div class="info-text">
                        <span class="title-text">Total</span>
                        <span class="title-content">"""+str(un_contrat.fraisdossiertot)+"""</span>
                    </div>
                </div>

                <div class="lg-c12 md-c12 sm-c12 xs-c12">
                    <h4  class="cl-primary">Frais d'assurance</h4><br>
                </div>

                <div class="lg-c3 md-c3 sm-c6 xs-c12">
                    <div class="info-text">
                        <span class="title-text">Montant</span>
                        <span class="title-content">"""+str(un_contrat.assurancemtt)+"""</span>
                    </div>
                </div>
                <div class="lg-c3 md-c3 sm-c6 xs-c12">
                    <div class="info-text">
                        <span class="title-text">Qté</span>
                        <span class="title-content">"""+str(un_contrat.assuranceqte)+"""</span>
                    </div>
                </div>
                <div class="lg-c3 md-c3 sm-c6 xs-c12">
                    <div class="info-text">
                        <span class="title-text">TVA</span>
                        <span class="title-content">"""+str(un_contrat.assurancetva)+"""</span>
                    </div>
                </div>
                <div class="lg-c3 md-c3 sm-c6 xs-c12">
                    <div class="info-text">
                        <span class="title-text">Total</span>
                        <span class="title-content">"""+str(un_contrat.assurancetot)+"""</span>
                    </div>
                </div>

                <div class="lg-c12 md-c12 sm-c12 xs-c12">
                    <div class="info-text">
                        <span class="title-text cl-primary">Etat contrat</span>
                        <span class="title-content">"""+str(etatcontrat)+"""</span>
                    </div>
                </div>
                
            </div>
        """
    data = {
        'un_contrat':html_data
    }
    return JsonResponse(data)

def closeContrat(request):
    if request.method == 'GET':
        id = request.GET.get('id',False)
        objs = request.GET.get('objs',False)
        un_contrat = get_object_or_404(Contrat, idpub=id)

        if un_contrat.typecontrat == 1:
            typecontrat = 'Contrat de bail habitation'
        else:
            typecontrat = 'Contrat de bail commercial'
        if objs == '1':
            html_data = """
                <div class="row-view"> 
                    <div class="lg-c12 md-c12 sm-c6 xs-c12">
                        <div class="info-text">
                            <span class="title-content">Confirmer l'arret du """+str(typecontrat)+' (<b>'+str(un_contrat.refcontrat)+"""</b>)</span>
                        </div>
                    </div>
                    <div class="lg-c12 md-c12 sm-c6 xs-c12">
                        <div class="info-text">
                            <i style="color:red;">Il n'y a pas de retour en arrière après confirmation</i>
                        </div>
                    </div>
                </div>
            """
        else:
            html_data = """
                <div class="row-view"> 
                    <div class="lg-c12 md-c12 sm-c6 xs-c12">
                        <div class="info-text">
                            <span class="title-content">Confirmer la suppression du """+str(typecontrat)+' (<b>'+str(un_contrat.refcontrat)+"""</b>)</span>
                        </div>
                    </div>
                </div>
            """
    data = {
        'un_contrat':html_data
    }
    return JsonResponse(data)

def delContrat(request):
    if request.method == 'POST':
        id = request.POST.get('arretcontratid',False)
        objs = request.POST.get('contratobjs',False)
        
        if int(objs) == 1:
            Contrat.objects.filter(idpub=id).update(
                activecontrat = 2,
                datefin = datetime.today()
            )
            un_contrat = Contrat.objects.get(idpub=id)
            Locative.objects.filter(id=un_contrat.locative.id).update(
                etat = 1
            )
            
        else:
            Facture.objects.filter(contrat__idpub=id).delete()
            un_contrat = Contrat.objects.get(idpub=id)
            Locative.objects.filter(id=un_contrat.locative.id).update(
                etat = 1
            )
            Contrat.objects.filter(idpub=id).delete()
            
            

    data = {
        'id': 1
    }
    return JsonResponse(data)


def pdfcontrat(request):
    if Proprietaire.objects.filter(user=request.user).exists():
        liste_contrat = Contrat.objects.filter(proprietaire_id=request.user.proprietaire.id).order_by('creation')
    elif Locataire.objects.filter(user=request.user).exists():
        liste_contrat = Contrat.objects.filter(locataire_id=request.user.locataire.id).order_by('creation')
    else:
        liste_contrat = Contrat.objects.all().order_by('creation')

    contentdata = {
        'etablissement': Etablissement.objects.get(id=Etablissement.objects.last().id),
        "date": datetime.now(),
        'filenom':"LISTE_CONTRAT_"+str(datetime.now()),
        'today': datetime.now(),
        'action': request.user.username,
        'liste_contrat' : liste_contrat
    }
        
    template = get_template('gimmo/pages/contrat/pdf-file.html')
    html = template.render(contentdata)

    result = BytesIO()
    pdf = pisa.pisaDocument(BytesIO(html.encode("utf-8")),result)
    if not pdf.err:
        response = HttpResponse(result.getvalue(),content_type='application/pdf')
        filename = "LISTE_CONTRAT_"+str(datetime.now())+".pdf"
        response['Content-Disposition'] = "attachment; filename="+filename
        return response
        
    return None

def pdfuncontrat(request,pk):
    un_contrat = Contrat.objects.get(idpub=pk)
    contentdata = {
        'etablissement': Etablissement.objects.get(id=Etablissement.objects.last().id),
        "date": datetime.now(),
        'filenom':"CONTRAT_"+str(un_contrat.refcontrat),
        'today': datetime.now(),
        'action': request.user.username,
        'un_contrat' : un_contrat
    }
        
    template = get_template('gimmo/pages/contrat/pdf-info.html')
    html = template.render(contentdata)

    result = BytesIO()
    pdf = pisa.pisaDocument(BytesIO(html.encode("utf-8")),result)
    if not pdf.err:
        response = HttpResponse(result.getvalue(),content_type='application/pdf')
        filename = "CONTRAT_"+str(un_contrat.refcontrat)+".pdf"
        response['Content-Disposition'] = "attachment; filename="+filename
        return response
        
    return None

def exporterfac(request,pk):
    une_facture = Facture.objects.get(idpub=pk)
    contentdata = {
        'etablissement': Etablissement.objects.get(id=Etablissement.objects.last().id),
        "date": datetime.now(),
        'filenom':"FACTURE_"+str(une_facture.reffacture),
        'today': datetime.now(),
        'action': request.user.username,
        'une_facture' : une_facture,
        'totlettre':num2words(une_facture.payefacture, lang='fr')
    }
    if une_facture.typefacture == 'Avance/Caution':    
        template = get_template('gimmo/pages/paiement/pdf-info.html')
    else:
        template = get_template('gimmo/pages/paiement/pdf-info-p.html')

    html = template.render(contentdata)

    result = BytesIO()
    pdf = pisa.pisaDocument(BytesIO(html.encode("utf-8")),result)
    if not pdf.err:
        response = HttpResponse(result.getvalue(),content_type='application/pdf')
        filename = "FACTURE_"+str(une_facture.reffacture)+".pdf"
        response['Content-Disposition'] = "attachment; filename="+filename
        return response
        
    return None

def exporterrec(request,pk):
    une_facture = Facture.objects.get(idpub=pk)
    contentdata = {
        'etablissement': Etablissement.objects.get(id=Etablissement.objects.last().id),
        "date": datetime.now(),
        'filenom':"RECU_"+str(une_facture.reffacture),
        'today': datetime.now(),
        'action': request.user.username,
        'une_facture' : une_facture,
        'totlettre':num2words(une_facture.payefacture, lang='fr')
    }
    
    if une_facture.typefacture == 'Avance/Caution': 
        template = get_template('gimmo/pages/rapport/pdf-info.html')
    else:
        template = get_template('gimmo/pages/rapport/pdf-info-p.html')

    html = template.render(contentdata)

    result = BytesIO()
    pdf = pisa.pisaDocument(BytesIO(html.encode("utf-8")),result)
    if not pdf.err:
        response = HttpResponse(result.getvalue(),content_type='application/pdf')
        filename = "RECU_"+str(une_facture.reffacture)+".pdf"
        response['Content-Disposition'] = "attachment; filename="+filename
        return response
        
    return None

def exporterunefac(request,pk):
    une_facture = Facturedetails.objects.get(idpub=pk)
    contentdata = {
        'etablissement': Etablissement.objects.get(id=Etablissement.objects.last().id),
        "date": datetime.now(),
        'filenom':"RECU_"+str(une_facture.facture.reffacture),
        'today': datetime.now(),
        'action': request.user.username,
        'une_facture' : une_facture,
        'totlettre':num2words(une_facture.paye, lang='fr')
    }
        
    template = get_template('gimmo/pages/paiement/pdf-un-info.html')
    html = template.render(contentdata)

    result = BytesIO()
    pdf = pisa.pisaDocument(BytesIO(html.encode("utf-8")),result)
    if not pdf.err:
        response = HttpResponse(result.getvalue(),content_type='application/pdf')
        filename = "RECU_"+str(une_facture.facture.reffacture)+".pdf"
        response['Content-Disposition'] = "attachment; filename="+filename
        return response
        
    return None
####paiement
@login_required(login_url='/')
def paiement(request):
    etat = 0
    if Proprietaire.objects.filter(user=request.user).exists():
        liste_facture = Facture.objects.filter(etat__gte=2,contrat__proprietaire__id=Proprietaire.objects.get(user=request.user).id).order_by('creation')
        #liste_locative = Contrat.objects.values('locative__reflocative','bien__adresse','bien__ville','bien__quartier','locative__superficie','locative__typelocative','locative__etat','locative__montant','locative__charge','locative__idpub','locative__id').annotate(dcount=Count('locataire')).filter(proprietaire_id=Proprietaire.objects.get(user=request.user).id).order_by()

        totala = Facture.objects.filter(etat__gte=2,contrat__proprietaire__id=Proprietaire.objects.get(user=request.user).id).aggregate(tot=Sum('totfacture'))
        totala = totala['tot']
        if totala == None:
            totala = 0
        else:
            totala = totala

        totalp = Facture.objects.filter(etat__gte=2,contrat__proprietaire__id=Proprietaire.objects.get(user=request.user).id).aggregate(tot=Sum('payefacture'))
        totalp = totalp['tot']
        if totalp == None:
            totalp = 0
        else:
            totalp = totalp
        
        totalr = Facture.objects.filter(etat__gte=2,contrat__proprietaire__id=Proprietaire.objects.get(user=request.user).id).aggregate(tot=Sum('restefacture'))
        totalr = totalr['tot']
        if totalr == None:
            totalr = 0
        else:
            totalr = totalr
    elif Locataire.objects.filter(user=request.user).exists():
        liste_facture = Facture.objects.filter(etat__gte=2,locataire_id=Locataire.objects.get(user=request.user).id).order_by('creation')

        totala = Facture.objects.filter(etat__gte=2,locataire_id=Locataire.objects.get(user=request.user).id).aggregate(tot=Sum('totfacture'))
        totala = totala['tot']
        if totala == None:
            totala = 0
        else:
            totala = totala

        totalp = Facture.objects.filter(etat__gte=2,locataire_id=Locataire.objects.get(user=request.user).id).aggregate(tot=Sum('payefacture'))
        totalp = totalp['tot']
        if totalp == None:
            totalp = 0
        else:
            totalp = totalp
        
        totalr = Facture.objects.filter(etat__gte=2,locataire_id=Locataire.objects.get(user=request.user).id).aggregate(tot=Sum('restefacture'))
        totalr = totalr['tot']
        if totalr == None:
            totalr = 0
        else:
            totalr = totalr
    else:
        liste_facture = Facture.objects.filter(etat__gte=2).order_by('creation')

        totala = Facture.objects.filter(etat__gte=2).aggregate(tot=Sum('totfacture'))
        totala = totala['tot']
        if totala == None:
            totala = 0
        else:
            totala = totala

        totalp = Facture.objects.filter(etat__gte=2).aggregate(tot=Sum('payefacture'))
        totalp = totalp['tot']
        if totalp == None:
            totalp = 0
        else:
            totalp = totalp
        
        totalr = Facture.objects.filter(etat__gte=2).aggregate(tot=Sum('restefacture'))
        totalr = totalr['tot']
        if totalr == None:
            totalr = 0
        else:
            totalr = totalr

    content = {
        'etat':etat,
        'paiement': True,
        'liste_facture':liste_facture,
        'totala':totala,
        'totalp':totalp,
        'totalr':totalr
    }
    return render(request,'gimmo/pages/paiement/paiement.html',content)

####payer
@login_required(login_url='/')
def payer(request):
    etat = 0
    if Proprietaire.objects.filter(user=request.user).exists():
        liste_contrat = Contrat.objects.filter(activecontrat=1,proprietaire_id=request.user.proprietaire.id).order_by('creation')
    elif Locataire.objects.filter(user=request.user).exists():
        liste_contrat = Contrat.objects.filter(activecontrat=1,locataire_id=request.user.locataire.id).order_by('creation')
    else:
        liste_contrat = Contrat.objects.filter(activecontrat=1).order_by('creation')
    content = {
        'etat':etat,
        #'paiement': True,
        'liste_contrat':liste_contrat
    }
    return render(request,'gimmo/pages/paiement/payer.html',content)

def payinfo(request):
    if request.method == 'GET':
        idpub = request.GET.get('idpub',False)
        un_contrat = Contrat.objects.get(idpub=idpub)
        solde = un_contrat.locative.montant+un_contrat.locative.charge
        ppay = un_contrat.prochainpay
        
    data = {
        'solde': solde,
        'ppay': ppay
    }
    return JsonResponse(data)


def payerloyer(request):
    if request.method == 'POST':
        typepay = request.POST.get('typepay',False)
        mois = request.POST.get('mois',False)
        iddpub = request.POST.get('iddpub',False)

        un_contrat = Contrat.objects.get(idpub=iddpub)


        count_tab_facture = Facture.objects.all().count()
        idpub_facture = uuid.uuid4()
        idpub_facture = str(idpub_facture).replace("-","")
        publicid_facture = idpub_facture + str(count_tab_facture)
        ref_facture = 'FT26-'+str(count_tab_facture)
        typefacture = un_contrat.prochainpay

        Facture.objects.create(
            idpub = publicid_facture,
            reffacture = ref_facture,
            typefacture = typefacture,
            dureepay = int(mois),
            debutpay = un_contrat.prochainpay,
            finpay = un_contrat.prochainpay,
            totfacture = int(mois)*(un_contrat.locative.montant+un_contrat.locative.charge),
            payefacture = int(mois)*(un_contrat.locative.montant+un_contrat.locative.charge),
            restefacture = 0,
            retardfacture = 0,
            finaltotal = int(mois)*(un_contrat.locative.montant+un_contrat.locative.charge),
            etat = 1,
            locataire = Locataire.objects.get(id=int(un_contrat.locataire.id)),
            locative = Locative.objects.get(id=int(un_contrat.locative.id)),
            contrat = Contrat.objects.get(refcontrat=un_contrat.refcontrat),
            creation = datetime.now()
        ).save()
        
        
        count_tab = Facturedetails.objects.all().count()
        idpub_ref = uuid.uuid4()
        idpub_ref = str(idpub_ref).replace("-","")
        publicid = idpub_ref + str(count_tab)
        
        reftrans = 'FDT26-'+str(count_tab)

        une_facture = Facture.objects.get(idpub=publicid_facture)
        Facturedetails.objects.create(
            idpub = publicid,
            reftrans = reftrans,
            paye = int(mois)*(un_contrat.locative.montant+un_contrat.locative.charge),
            reste = une_facture.restefacture,
            typetrans = int(typepay),
            etat = 1,
            facture = Facture.objects.get(id=int(une_facture.id)),
            creation = datetime.now()
        ).save()

        #PROCHAIN PAIEMENT
        date_pay = Contrat.objects.get(idpub=iddpub).prochainpay
        date_pay_sd = pd.to_datetime(date_pay)
        second_pay = date_pay_sd+pd.DateOffset(months=int(mois))


        Contrat.objects.filter(idpub=iddpub).update(
            prochainpay = second_pay
        )
        Facture.objects.filter(idpub=publicid_facture).update(
            finpay = second_pay
        )
        
    data = {
    }
    return JsonResponse(data)


@login_required(login_url='/')
def facture(request,pk):
    etat = 0
    une_facture = get_object_or_404(Facture, reffacture=pk)
    liste_facture_d = Facturedetails.objects.filter(facture=une_facture.id).order_by('-creation')

    totalp = Facture.objects.filter(reffacture=pk).aggregate(tot=Sum('payefacture'))
    totalp = totalp['tot']
    if totalp == None:
        totalp = 0
    else:
        totalp = totalp
    
    totalr = Facture.objects.filter(reffacture=pk).aggregate(tot=Sum('restefacture'))
    totalr = totalr['tot']
    if totalr == None:
        totalr = 0
    else:
        totalr = totalr
    
    if Proprietaire.objects.filter(user=request.user).exists():
        etat_paiement = 1
    elif Locataire.objects.filter(user=request.user).exists():
        etat_paiement = 2
    else:
        etat_paiement = 0

    content = {
        'etat':etat,
        'paiement': True,
        'une_facture':une_facture,
        'liste_facture_d':liste_facture_d,
        'totalr':totalr,
        'totalp':totalp,
        'un_etablissement':Etablissement.objects.get(id=Etablissement.objects.last().id),
        'etat_paiement':etat_paiement
    }
    return render(request,'gimmo/pages/paiement/facture.html',content)

def ajxfacture(request):
    etat = 0
    
    if request.method == "POST":
        montant = request.POST.get('montant',False)
        typepay = request.POST.get('typepay',False)
        idpub = request.POST.get('idpub',False)
        
        Facture.objects.filter(idpub=idpub).update(
            payefacture = (F('payefacture') + montant),
            restefacture = (F('restefacture') - montant)
        )
        Contrat.objects.filter(id=Facture.objects.get(idpub=idpub).contrat_id).update(
            activecontrat=1
        )
        Locative.objects.filter(id=Facture.objects.get(idpub=idpub).locative.id).update(
            etat = 2
        )

        count_tab = Facturedetails.objects.all().count()
        idpub_ref = uuid.uuid4()
        idpub_ref = str(idpub_ref).replace("-","")
        publicid = idpub_ref + str(count_tab)
        
        reftrans = 'FDT26-'+str(count_tab)

        une_facture = Facture.objects.get(idpub=idpub)
        Facturedetails.objects.create(
            idpub = publicid,
            reftrans = reftrans,
            paye = montant,
            reste = une_facture.restefacture,
            typetrans = int(typepay),
            etat = 1,
            facture = Facture.objects.get(id=int(une_facture.id)),
            creation = datetime.now()
        ).save()

        #PROCHAIN PAIEMENT
        date_pay = Contrat.objects.get(id=Facture.objects.get(idpub=idpub).contrat_id).prochainpay
        date_pay_sd = pd.to_datetime(date_pay)
        second_pay = date_pay_sd+pd.DateOffset(months=1)

        Facture.objects.filter(idpub=idpub).update(
            debutpay =  Contrat.objects.get(id=Facture.objects.get(idpub=idpub).contrat_id).prochainpay,
            finpay = second_pay
        )


        if une_facture.restefacture == 0:
            statut_facture = 1
            Contrat.objects.filter(id=Facture.objects.get(idpub=idpub).contrat_id).update(
                prochainpay = second_pay
            )
        else:
            statut_facture = 4

        Facture.objects.filter(idpub=idpub).update(
            etat = statut_facture
        )
        etat = 1
    
    data = {
        'etat': etat
    }
    return JsonResponse(data)


def pdfpaiement(request):
    if Proprietaire.objects.filter(user=request.user).exists():
        liste_facture = Facture.objects.filter(etat__gte=2).order_by('creation')

        totala = Facture.objects.filter(etat__gte=2).aggregate(tot=Sum('finaltotal'))
        totala = totala['tot']
        if totala == None:
            totala = 0
        else:
            totala = totala

        totalp = Facture.objects.filter(etat__gte=2).aggregate(tot=Sum('payefacture'))
        totalp = totalp['tot']
        if totalp == None:
            totalp = 0
        else:
            totalp = totalp
        
        totalr = Facture.objects.filter(etat__gte=2).aggregate(tot=Sum('restefacture'))
        totalr = totalr['tot']
        if totalr == None:
            totalr = 0
        else:
            totalr = totalr
    elif Locataire.objects.filter(user=request.user).exists():
        liste_facture = Facture.objects.filter(etat__gte=2).order_by('creation')

        totala = Facture.objects.filter(etat__gte=2).aggregate(tot=Sum('finaltotal'))
        totala = totala['tot']
        if totala == None:
            totala = 0
        else:
            totala = totala

        totalp = Facture.objects.filter(etat__gte=2).aggregate(tot=Sum('payefacture'))
        totalp = totalp['tot']
        if totalp == None:
            totalp = 0
        else:
            totalp = totalp
        
        totalr = Facture.objects.filter(etat__gte=2).aggregate(tot=Sum('restefacture'))
        totalr = totalr['tot']
        if totalr == None:
            totalr = 0
        else:
            totalr = totalr
    else:
        liste_facture = Facture.objects.filter(etat__gte=2).order_by('creation')

        totala = Facture.objects.filter(etat__gte=2).aggregate(tot=Sum('finaltotal'))
        totala = totala['tot']
        if totala == None:
            totala = 0
        else:
            totala = totala

        totalp = Facture.objects.filter(etat__gte=2).aggregate(tot=Sum('payefacture'))
        totalp = totalp['tot']
        if totalp == None:
            totalp = 0
        else:
            totalp = totalp
        
        totalr = Facture.objects.filter(etat__gte=2).aggregate(tot=Sum('restefacture'))
        totalr = totalr['tot']
        if totalr == None:
            totalr = 0
        else:
            totalr = totalr

    contentdata = {
        'etablissement': Etablissement.objects.get(id=Etablissement.objects.last().id),
        "date": datetime.now(),
        'filenom':"LISTE_PAIEMENT_"+str(datetime.now()),
        'today': datetime.now(),
        'action': request.user.username,
        'liste_facture':liste_facture,
        'totala':totala,
        'totalp':totalp,
        'totalr':totalr
    }
        
    template = get_template('gimmo/pages/paiement/pdf-file.html')
    html = template.render(contentdata)

    result = BytesIO()
    pdf = pisa.pisaDocument(BytesIO(html.encode("utf-8")),result)
    if not pdf.err:
        response = HttpResponse(result.getvalue(),content_type='application/pdf')
        filename = "LISTE_PAIEMENT_"+str(datetime.now())+".pdf"
        response['Content-Disposition'] = "attachment; filename="+filename
        return response
        
    return None


####paiement a venir
@login_required(login_url='/')
def paiementav(request):
    etat = 0
    annee_encours = date.today().year
    mois_svt = int(date.today().month)+1
    if mois_svt == 13:
        mois_svt = 1
    else:
        mois_svt = mois_svt

    tab_mois = [
        'Janvier',
        'Février',
        'Mars',
        'Avril',
        'Mai',
        'Juin',
        'Juillet',
        'Aout',
        'Septembre',
        'Octobre',
        'Novembre',
        'Décembre'
    ]
    
    #AUTO LOYER
    #for un_contrat in list_contrat:
    #    une_locative = un_contrat.locative.montant
    #    frais_sur_une_locative = un_contrat.locative.charge
    #    loyer = une_locative + frais_sur_une_locative

    if Proprietaire.objects.filter(user=request.user).exists():
        liste_facture = Contrat.objects.filter(activecontrat=1,proprietaire_id=Proprietaire.objects.get(user=request.user).id).order_by()

        total = Contrat.objects.filter(activecontrat=1,proprietaire_id=Proprietaire.objects.get(user=request.user).id).aggregate(fraisLoyer=Sum('locative__montant'),fraisSurLoyer=Sum('locative__charge'))

        total_frais_loyer = total['fraisLoyer']
        total_frais_sur_loyer = total['fraisSurLoyer']

        if total_frais_loyer == None:
            total_frais_loyer = 0
        else:
            total_frais_loyer = total_frais_loyer
        
        if total_frais_sur_loyer == None:
            total_frais_sur_loyer = 0
        else:
            total_frais_sur_loyer = total_frais_sur_loyer
        
        total = total_frais_sur_loyer+total_frais_loyer

    elif Locataire.objects.filter(user=request.user).exists():
        liste_facture = Contrat.objects.filter(activecontrat=1,locataire_id=Locataire.objects.get(user=request.user).id).order_by()
        total = Contrat.objects.filter(activecontrat=1,proprietaire_id=Locataire.objects.get(user=request.user).id).aggregate(fraisLoyer=Sum('locative__montant'),fraisSurLoyer=Sum('locative__charge'))

        total_frais_loyer = total['fraisLoyer']
        total_frais_sur_loyer = total['fraisSurLoyer']

        if total_frais_loyer == None:
            total_frais_loyer = 0
        else:
            total_frais_loyer = total_frais_loyer
        
        if total_frais_sur_loyer == None:
            total_frais_sur_loyer = 0
        else:
            total_frais_sur_loyer = total_frais_sur_loyer
        
        total = total_frais_sur_loyer+total_frais_loyer
        
    else:
        liste_facture = Contrat.objects.filter(activecontrat=1).order_by()
        total = Contrat.objects.filter(activecontrat=1).aggregate(fraisLoyer=Sum('locative__montant'),fraisSurLoyer=Sum('locative__charge'))

        total_frais_loyer = total['fraisLoyer']
        total_frais_sur_loyer = total['fraisSurLoyer']

        if total_frais_loyer == None:
            total_frais_loyer = 0
        else:
            total_frais_loyer = total_frais_loyer
        
        if total_frais_sur_loyer == None:
            total_frais_sur_loyer = 0
        else:
            total_frais_sur_loyer = total_frais_sur_loyer
        
        total = total_frais_sur_loyer+total_frais_loyer

    content = {
        'etat':etat,
        'paiementav': True,
        'liste_facture':liste_facture,
        'mois_paiement': tab_mois[mois_svt],
        'total':total,
        'total_frais_loyer':total_frais_loyer,
        'total_frais_sur_loyer':total_frais_sur_loyer
        #'totala':totala,
        #'totalp':totalp,
        #'totalr':totalr
    }
    return render(request,'gimmo/pages/paiementav/paiementav.html',content)


####bien
@login_required(login_url='/')
def depense(request):
    etat = 0
    liste_depense = Depense.objects.all().order_by('creation')
    totald = Depense.objects.all().aggregate(tot=Sum('valeur'))
    totald = totald['tot']
    if totald == None:
        totald = 0
    else:
        totald = totald

    content = {
        'etat':etat,
        'depense': True,
        'liste_depense':liste_depense,
        'totald':totald
    }
    return render(request,'gimmo/pages/depenses/depense.html',content)

@login_required(login_url='/')
def newdepense(request):
    etat = 0
    content = {
        'etat':etat,
        'depense': True,
        'liste_proprietaire': Proprietaire.objects.filter(d1__gte=1).order_by('nom'),
        'liste_locataire': Locataire.objects.filter(d1__gte=1).order_by('nom')
    }
    return render(request,'gimmo/pages/depenses/newdepense.html',content)


@login_required(login_url='/')
def edepense(request,pk):
    etat = 0
    une_depense = get_object_or_404(Depense, idpub=pk)
    liste_proprietaire = Proprietaire.objects.filter(d1__gte=1).order_by('creation')

    content = {
        'etat':etat,
        'depense': True,
        'une_depense':une_depense,
        'liste_proprietaire':liste_proprietaire
    }
    return render(request,'gimmo/pages/depenses/edepense.html',content)

def eajxdepense(request):
    etat = 0
    
    if request.method == "POST":
        valeur = request.POST.get('valeur',False)
        description = request.POST.get('description',False)
        proprietaire = request.POST.get('proprietaire',False)
        bien = request.POST.get('bien',False)
        locative = request.POST.get('locative',False)
        idpub = request.POST.get('idpub',False)

        if locative == False or locative == '':
            locative = 0
        else:
            locative = locative
        
        Depense.objects.filter(idpub=idpub).update(
            valeur = valeur,
            description = description,
            proprietaire = Proprietaire.objects.get(id=int(proprietaire)),
            bien = Bien.objects.get(id=int(bien)),
            locative = locative,
            user = request.user
        )
        etat = 1
    
    data = {
        'etat': etat
    }
    return JsonResponse(data)

def ajxdepense(request):
    etat = 0
    
    if request.method == "POST":
        valeur = request.POST.get('valeur',False)
        description = request.POST.get('description',False)
        proprietaire = request.POST.get('proprietaire',False)
        bien = request.POST.get('bien',False)
        locative = request.POST.get('locative',False)

        if locative == False or locative == '':
            locative = 0
        else:
            locative = locative
        
        
        count_tab = Depense.objects.all().count()
        idpub = uuid.uuid4()
        idpub = str(idpub).replace("-","")
        publicid = idpub + str(count_tab)
        refdep = 'DEP26-'+str(count_tab)
        
        Depense.objects.create(
            idpub = publicid,
            refdep = refdep,
            valeur = valeur,
            description = description,
            etat = 1,
            proprietaire = Proprietaire.objects.get(id=int(proprietaire)),
            bien = Bien.objects.get(id=int(bien)),
            locative = locative,
            user = request.user,
            creation = datetime.now()
        ).save()
        etat = 1
    
    data = {
        'etat': etat
    }
    return JsonResponse(data)

def desdepense(request):
    if request.method == 'GET':
        id = request.GET.get('id',False)
        une_depense = get_object_or_404(Depense, idpub=id)
        info_depense = une_depense.description
        
        text = "Confirmer la suppression de la dépense <b>"""+info_depense+"</b>"
        
    data = {
        'text': text
    }
    return JsonResponse(data)

def deldepense(request):
    etat = 0
    if request.method == 'POST':
        id = request.POST.get('deldepense',False)
        Depense.objects.filter(idpub=id).delete()
        etat = 1

    data = {
        'etat': etat
    }
    return JsonResponse(data)

def pdfdepense(request):
    liste_depense = Depense.objects.all().order_by('creation')
    totald = Depense.objects.all().aggregate(tot=Sum('valeur'))
    totald = totald['tot']
    if totald == None:
        totald = 0
    else:
        totald = totald
    contentdata = {
        'etablissement': Etablissement.objects.get(id=Etablissement.objects.last().id),
        "date": datetime.now(),
        'filenom':"LISTE_DEPENSE_"+str(datetime.now()),
        'today': datetime.now(),
        'action': request.user.username,
        'liste_depense' : liste_depense,
        'totald':totald
    }
        
    template = get_template('gimmo/pages/depenses/pdf-file.html')
    html = template.render(contentdata)

    result = BytesIO()
    pdf = pisa.pisaDocument(BytesIO(html.encode("utf-8")),result)
    if not pdf.err:
        response = HttpResponse(result.getvalue(),content_type='application/pdf')
        filename = "LISTE_DEPENSE_"+str(datetime.now())+".pdf"
        response['Content-Disposition'] = "attachment; filename="+filename
        return response
        
    return None

def pdfunedepense(request,pk):
    une_depense = Depense.objects.get(idpub=pk)
    contentdata = {
        'etablissement': Etablissement.objects.get(id=Etablissement.objects.last().id),
        "date": datetime.now(),
        'filenom':"DEPENSE_"+str(une_depense.description),
        'today': datetime.now(),
        'action': request.user.username,
        'une_depense' : une_depense
    }
        
    template = get_template('gimmo/pages/depenses/pdf-info.html')
    html = template.render(contentdata)

    result = BytesIO()
    pdf = pisa.pisaDocument(BytesIO(html.encode("utf-8")),result)
    if not pdf.err:
        response = HttpResponse(result.getvalue(),content_type='application/pdf')
        filename = "DEPENSE_"+str(une_depense.description)+".pdf"
        response['Content-Disposition'] = "attachment; filename="+filename
        return response
        
    return None

####fichier
@login_required(login_url='/')
def fichier(request):
    etat = 0
    list_fichier = Fichier.objects.all().order_by('creation')

    content = {
        'etat':etat,
        'fichier': True,
        'list_fichier':list_fichier
    }
    return render(request,'gimmo/pages/fichier/fichier.html',content)

def ajxfichier(request):
    etat = 0
    
    if request.method == "POST":
        nom = request.POST.get('nom',False)

        if request.FILES.get('fichier', False):
            im1 = request.FILES['fichier']
            fichier = FileSystemStorage()
            fichier = fichier.save(im1.name, im1)
        else:
            fichier = ""
        
        count_tab = Fichier.objects.all().count()
        idpub = uuid.uuid4()
        idpub = str(idpub).replace("-","")
        publicid = idpub + str(count_tab)
        
        Fichier.objects.create(
            idpub = publicid,
            etat = 1,
            nom = nom,
            fichier = fichier,
            user = request.user,
            creation = datetime.now()
        ).save()
        etat = 1
    
    data = {
        'etat': etat
    }
    return JsonResponse(data)

def downfichier(request,pk):
    un_fichier = Fichier.objects.get(idpub=pk)
    path = un_fichier.fichier.path
    file_path = os.path.join(settings.MEDIA_ROOT,path)
    name,extension = os.path.splitext(un_fichier.fichier.name)
    application_tp = str(extension).replace(".","")
    
    if os.path.exists(file_path):
        with open(file_path,'rb') as fh:
            response = HttpResponse(fh.read(),content_type="application/"+str(application_tp))
            response['Content-Disposition'] = 'inline;filename='+str(un_fichier.nom)+''+str(extension)
            return response
    return None


####message
@login_required(login_url='/')
def message(request):
    etat = 0
    list_utilisateur = User.objects.filter(is_staff=0).order_by('first_name')

    content = {
        'etat':etat,
        'message': True,
        'list_utilisateur':(list_utilisateur)
    }
    return render(request,'gimmo/pages/message/message.html',content)

def get_sms_user(request):
    etat = 0
    if request.method == 'GET':
        id = request.GET.get('sms_user',False)

        if Proprietaire.objects.filter(user_id=id).exists():
            nom = Proprietaire.objects.get(user_id=id).nom
            prenom = Proprietaire.objects.get(user_id=id).prenom
            user_type = 'Propriétaire'

        elif Locataire.objects.filter(user_id=id).exists():
            nom = Locataire.objects.get(user_id=id).nom
            prenom = Locataire.objects.get(user_id=id).prenom
            user_type = 'Locataire'

        elif Employe.objects.filter(user_id=id).exists():
            nom = Employe.objects.get(user_id=id).nom
            prenom = Employe.objects.get(user_id=id).prenoms
            user_type = 'Personnel'

        else:
            nom = 'None'
            prenom = ''
            user_type = 'None'

        etat = 1
            

    data = {
        'etat': etat,
        'nom_prenom':str(nom.upper())+' '+str(prenom),
        'user_type':user_type
    }
    return JsonResponse(data)

####rapport
@login_required(login_url='/')
def rapport(request):
    etat = 0
    if Locataire.objects.filter(user=request.user).exists():
        liste_facture = Facture.objects.filter(etat__lte=1,locataire_id=request.user.locataire.id).order_by('creation')

        totala = Facture.objects.filter(etat__lte=1,locataire_id=request.user.locataire.id).aggregate(tot=Sum('finaltotal'))
        totala = totala['tot']
        if totala == None:
            totala = 0
        else:
            totala = totala

        totalp = Facture.objects.filter(etat__lte=1,locataire_id=request.user.locataire.id).aggregate(tot=Sum('payefacture'))
        totalp = totalp['tot']
        if totalp == None:
            totalp = 0
        else:
            totalp = totalp
        
        totalr = Facture.objects.filter(etat__lte=1,locataire_id=request.user.locataire.id).aggregate(tot=Sum('restefacture'))
        totalr = totalr['tot']
        if totalr == None:
            totalr = 0
        else:
            totalr = totalr
    elif Proprietaire.objects.filter(user=request.user).exists():
        liste_facture = Facture.objects.filter(etat__lte=1,contrat__proprietaire__id=Proprietaire.objects.get(user=request.user).id).order_by('creation')

        totala = Facture.objects.filter(etat__lte=1,contrat__proprietaire__id=Proprietaire.objects.get(user=request.user).id).aggregate(tot=Sum('finaltotal'))
        totala = totala['tot']
        if totala == None:
            totala = 0
        else:
            totala = totala

        totalp = Facture.objects.filter(etat__lte=1,contrat__proprietaire__id=Proprietaire.objects.get(user=request.user).id).aggregate(tot=Sum('payefacture'))
        totalp = totalp['tot']
        if totalp == None:
            totalp = 0
        else:
            totalp = totalp
        
        totalr = Facture.objects.filter(etat__lte=1,contrat__proprietaire__id=Proprietaire.objects.get(user=request.user).id).aggregate(tot=Sum('restefacture'))
        totalr = totalr['tot']
        if totalr == None:
            totalr = 0
        else:
            totalr = totalr
    else:
        liste_facture = Facture.objects.filter(etat__lte=1).order_by('creation')

        totala = Facture.objects.filter(etat__lte=1).aggregate(tot=Sum('finaltotal'))
        totala = totala['tot']
        if totala == None:
            totala = 0
        else:
            totala = totala

        totalp = Facture.objects.filter(etat__lte=1).aggregate(tot=Sum('payefacture'))
        totalp = totalp['tot']
        if totalp == None:
            totalp = 0
        else:
            totalp = totalp
        
        totalr = Facture.objects.filter(etat__lte=1).aggregate(tot=Sum('restefacture'))
        totalr = totalr['tot']
        if totalr == None:
            totalr = 0
        else:
            totalr = totalr

    content = {
        'etat':etat,
        'rapport': True,
        'liste_facture':liste_facture,
        'totala':totala,
        'totalp':totalp,
        'totalr':totalr
    }
    return render(request,'gimmo/pages/rapport/rapport.html',content)

def detailPaiem(request):
    if request.method == 'GET':
        id = request.GET.get('id',False)
        une_facture = get_object_or_404(Facture, idpub=id)
        liste_recu = Facturedetails.objects.filter(facture_id=une_facture.id)

        html_data = """
            <table id="table_id" style="width:100%;" cellspacing="5">
                <thead>
                    <tr>
                        <th>#</th>
                        <th>Montant total</th>
                        <th>Payé</th>
                        <th>Reste</th>
                        <th>Mode paiement</th>
                        <th>Traité le</th>
                        <th>Statut</th>
                    </tr>
                </thead>
                <tbody>
            """
        counter = 0
        for un_recu in liste_recu:
            counter += 1

            html_data += """
                <tr style="padding-top: 10px;">
                    <td data-thead="#">"""+str(counter)+"""</td>
                    <td data-thead="Montant total">"""+str(un_recu.facture.finaltotal)+"""</td>
                    <td data-thead="Payé">"""+str(un_recu.paye)+"""</td>
                    <td data-thead="Reste">"""+str(un_recu.reste)+"""</td>
                    <td data-thead="Mode paiement">"""
            if un_recu.typetrans == 1:
                html_data += """Espèces"""
            elif un_recu.typetrans == 2:
                html_data += """Mobile"""
            elif un_recu.typetrans == 3:
                html_data += """Bancaire"""
            else:
                html_data += """Wallet"""

            html_data += """</td>
                    <td data-thead="Traité le">"""+str(un_recu.creation)+"""</td>
                    <td data-thead="Statut">"""
            if un_recu.etat == 1:
                html_data += """<span class="success">Succès</span>"""
            else:
                html_data += """<span class="danger">Erreur</span>"""
                        
            html_data += """</td>
                </tr>"""
        html_data += """
                </tbody>
            </table>"""

    data = {
        'un_recu':html_data
    }
    return JsonResponse(data)


def pdfrapport(request):
    if Locataire.objects.filter(user=request.user).exists():
        liste_facture = Facture.objects.filter(etat__lte=1,locataire_id=request.user.locataire.id).order_by('creation')

        totala = Facture.objects.filter(etat__lte=1,locataire_id=request.user.locataire.id).aggregate(tot=Sum('finaltotal'))
        totala = totala['tot']
        if totala == None:
            totala = 0
        else:
            totala = totala

        totalp = Facture.objects.filter(etat__lte=1,locataire_id=request.user.locataire.id).aggregate(tot=Sum('payefacture'))
        totalp = totalp['tot']
        if totalp == None:
            totalp = 0
        else:
            totalp = totalp
        
        totalr = Facture.objects.filter(etat__lte=1,locataire_id=request.user.locataire.id).aggregate(tot=Sum('restefacture'))
        totalr = totalr['tot']
        if totalr == None:
            totalr = 0
        else:
            totalr = totalr
    elif Proprietaire.objects.filter(user=request.user).exists():
        liste_facture = Facture.objects.filter(etat__lte=1).order_by('creation')

        totala = Facture.objects.filter(etat__lte=1).aggregate(tot=Sum('finaltotal'))
        totala = totala['tot']
        if totala == None:
            totala = 0
        else:
            totala = totala

        totalp = Facture.objects.filter(etat__lte=1).aggregate(tot=Sum('payefacture'))
        totalp = totalp['tot']
        if totalp == None:
            totalp = 0
        else:
            totalp = totalp
        
        totalr = Facture.objects.filter(etat__lte=1).aggregate(tot=Sum('restefacture'))
        totalr = totalr['tot']
        if totalr == None:
            totalr = 0
        else:
            totalr = totalr
    else:
        liste_facture = Facture.objects.filter(etat__lte=1).order_by('creation')

        totala = Facture.objects.filter(etat__lte=1).aggregate(tot=Sum('finaltotal'))
        totala = totala['tot']
        if totala == None:
            totala = 0
        else:
            totala = totala

        totalp = Facture.objects.filter(etat__lte=1).aggregate(tot=Sum('payefacture'))
        totalp = totalp['tot']
        if totalp == None:
            totalp = 0
        else:
            totalp = totalp
        
        totalr = Facture.objects.filter(etat__lte=1).aggregate(tot=Sum('restefacture'))
        totalr = totalr['tot']
        if totalr == None:
            totalr = 0
        else:
            totalr = totalr

    contentdata = {
        'etablissement': Etablissement.objects.get(id=Etablissement.objects.last().id),
        "date": datetime.now(),
        'filenom':"LISTE_RAPPORT_"+str(datetime.now()),
        'today': datetime.now(),
        'action': request.user.username,
        'liste_facture':liste_facture,
        'totala':totala,
        'totalp':totalp,
        'totalr':totalr
    }
        
    template = get_template('gimmo/pages/rapport/pdf-file.html')
    html = template.render(contentdata)

    result = BytesIO()
    pdf = pisa.pisaDocument(BytesIO(html.encode("utf-8")),result)
    if not pdf.err:
        response = HttpResponse(result.getvalue(),content_type='application/pdf')
        filename = "LISTE_RAPPORT_"+str(datetime.now())+".pdf"
        response['Content-Disposition'] = "attachment; filename="+filename
        return response
        
    return None


####parametre
@login_required(login_url='/')
def parametre(request):
    etat = 0
    un_etablissement = Etablissement.objects.get(id=Etablissement.objects.last().id)

    if str(un_etablissement.ouverture) == '2021-12-14':
        ouverture = ''
    else:
        ouverture = datetime.strptime(str(un_etablissement.ouverture), '%Y-%m-%d').strftime('%Y-%m-%d')

    content = {
        'etat':etat,
        'parametre': True,
        'un_etablissement':un_etablissement,
        'ouverture':ouverture
    }
    return render(request,'gimmo/pages/parametre/parametre.html',content)


def ajxetab(request):
    etat = 0
    un_etablissement = Etablissement.objects.get(id=Etablissement.objects.last().id)
    
    if request.method == "POST":
        #dataset = Dataset()
        raisonsocial = request.POST.get('raisonsocial',False)
        formejuridique = request.POST.get('formejuridique',False)
        comptecontribuable = request.POST.get('comptecontribuable',False)
        registrecommerce = request.POST.get('registrecommerce',False)
        secteur = request.POST.get('secteur',False)
        telfixe = request.POST.get('telfixe',False)
        tel = request.POST.get('tel',False)
        siege = request.POST.get('siege',False)
        adresse = request.POST.get('adresse',False)
        email = request.POST.get('email',False)
        devise = request.POST.get('devise',False)
        ouverture = request.POST.get('ouverture',False)

            
        if request.FILES.get('logo', False):
            im1 = request.FILES['logo']
            fs1 = FileSystemStorage()
            fs1 = fs1.save(im1.name, im1)
        else:
            fs1 = un_etablissement.logo
        
        if request.FILES.get('tampon', False):
            im2 = request.FILES['tampon']
            fs2 = FileSystemStorage()
            fs2 = fs2.save(im2.name, im2)
        else:
            fs2 = un_etablissement.tampon
        
        
        Etablissement.objects.filter(id=Etablissement.objects.last().id).update(
            raisonsocial = raisonsocial,
            formejuridique = formejuridique,
            comptecontribuable = comptecontribuable,
            registrecommerce = registrecommerce,
            secteur = secteur,
            telfixe = telfixe,
            tel = tel,
            siege = siege,
            adresse = adresse,
            email = email,
            devise = devise,
            ouverture = ouverture,
            logo = fs1,
            tampon = fs2
        )

        etat = 1
    
    data = {
        'etat': etat
    }
    return JsonResponse(data)

def ajxetabconfig(request):
    etat = 0
    
    if request.method == "POST":
        visitemtt = request.POST.get('visitemtt',False)
        honorairemtt = request.POST.get('honorairemtt',False)
        droitmtt = request.POST.get('droitmtt',False)
        timbremtt = request.POST.get('timbremtt',False)
        fraisdossiermtt = request.POST.get('fraisdossiermtt',False)
        assurancemtt = request.POST.get('assurancemtt',False)
        tva = request.POST.get('tva',False)
        margepay = request.POST.get('margepay',False)
        activepro = request.POST.get('activepro',False)
        activeloc = request.POST.get('activeloc',False)
        emailsend = request.POST.get('emailsend',False)
        smssend = request.POST.get('smssend',False)

        if activepro == False:
            activepro = False
        else:
            activepro = True

        if activeloc == False:
            activeloc = False
        else:
            activeloc = True

        if emailsend == False:
            emailsend = False
        else:
            emailsend = True

        if smssend == False:
            smssend = False
        else:
            smssend = True

            
       
        
        
        Etablissement.objects.filter(id=Etablissement.objects.last().id).update(
            visitemtt = visitemtt,
            honorairemtt = honorairemtt,
            droitmtt = droitmtt,
            timbremtt = timbremtt,
            fraisdossiermtt = fraisdossiermtt,
            assurancemtt = assurancemtt,
            tva = tva,
            margepay = int(margepay),
            activepro = activepro,
            activeloc = activeloc,
            emailsend = emailsend,
            smssend = smssend
        )

        etat = 1
    
    data = {
        'etat': etat
    }
    return JsonResponse(data)
####profile
@login_required(login_url='/')
def profile(request):
    etat = 0
    content = {
        'etat':etat
    }
    return render(request,'gimmo/pages/parametre/profile.html',content)

def updatemdp(request):
    etat = 0
    if request.method == 'POST':
        mdp = request.POST['mdp']
        mdpc = request.POST['mdpc']
        pseudo = request.POST['pseudo']
        if mdp == mdpc:
            u = User.objects.get(username=pseudo)
            u.set_password(mdp)
            u.save()
            etat = 1
        else:
            etat = 2
    
    data = {
        'etat':etat
    }
    return JsonResponse(data)

def infoprofile(request,pk):
    #response = HttpResponse(content_type='application/pdf')
    #response['Content-Disposition'] = 'inline; attachment; filename=example'+str(datetime.now())+'.pdf'
    #response['Content-transfer-Encoding'] = 'binary'

    contentdata = {
        "date": datetime.now(),
        'filenom':"LISTE_BIEN_"+str(datetime.now()),
        'today': datetime.now(),
        'action': request.user.username
        }
        
    template = get_template('gimmo/pages/bien/pdf-file.html')
    html = template.render(contentdata)

    result = BytesIO()
    pdf = pisa.pisaDocument(BytesIO(html.encode("utf-8")),result)
    if not pdf.err:
        response = HttpResponse(result.getvalue(),content_type='application/pdf')
        filename = "LISTE_BIEN_"+str(datetime.now())+".pdf"
        response['Content-Disposition'] = "attachment; filename="+filename
        return response
        
    return None

def themevar(request):
    etat = 0
    if Themevar.objects.filter(user=request.user).exists():
        un_theme = Themevar.objects.get(user=request.user)
        if un_theme.etat == 1:
            etat = 0
        else:
            etat = 1
        
        Themevar.objects.filter(user=request.user).update(
            etat = etat
        )
    else:
        Themevar.objects.create(
            etat = 1,
            user=request.user
        ).save()
    data = {
        'etat': etat
    }
    return JsonResponse(data)


def pay(request):
  content = {
    'TECHAGENCE_VAR': settings.TECHAGENCE_VAR
  }
  return render(request,'gimmo/pay/pay.html',content)

def abonnementtab(request):
    if request.method == 'POST':
        typeab =  int(request.POST.get('typeab',False))
        paiement_mob =  request.POST.get('paiement_mob',False)

        if typeab == 31:
            paiement_mob = 20500
            typeab_txt = '1 Mois'
            
        elif typeab == 186:
            paiement_mob = 20500*6
            typeab_txt = '6 Mois'
            
        elif typeab == 365:
            paiement_mob = 20500*12
            typeab_txt = '1 An'
            
        else:
            paiement_mob = 20500*60
            typeab_txt = '5 Ans'
            
        
        if paiement_mob == '1':
            paiement_mob = paiement_mob
        else:
            paiement_mob = 0
        

        totopay = paiement_mob
        
        
        
        data = {
            'typeab': typeab_txt,
            'paiement_mob': paiement_mob,
            'totopay':totopay
        }

    return JsonResponse(data)

def typeabonnement(request):
    if request.method == 'POST':
        typeab =  int(request.POST.get('typeab',False))
        print(typeab)

        if typeab == 31:
            typeab_txt = '1 Mois'
            montant = 20500
        
        elif typeab == 186:
            typeab_txt = '6 Mois'
            montant = 123000
        
        elif typeab == 370:
            typeab_txt = '1 An'
            montant = 246000
        
        else:
            typeab_txt = ''
            montant = 0
        

    data = {
        'typeab': typeab,
        'typeab_txt':typeab_txt,
        'montant': montant
        }

    return JsonResponse(data)


def demandeactivation(request):
    etat = 0
    if request.method == 'POST':
        typeab = request.POST.get('typeabcd',False)
        payvalue =  request.POST.get('payvalue',False)

        
        if typeab == False:
            typeab = 31
        else:
            typeab = typeab

        softk = uuid.uuid4()
        key_count = Tempsoftkeyactive.objects.all().count()
        if key_count == 0:
            Tempsoftkeyactive.objects.create(
                keyword = softk,
                typeab = int(typeab),
                etat = 0,
                datesoft = datetime.now()
            ).save()
        else:
            Tempsoftkeyactive.objects.filter(id=Tempsoftkeyactive.objects.last().id).update(
                keyword = softk,
                typeab = int(typeab),
                etat = 0,
                datesoft = datetime.now()
            )
        ##send mail to admin
        subject, from_email, to = 'DEMANDE ACTIVATION', settings.DEFAULT_FROM_EMAIL, settings.RECIPIENT_ADDRESS
        html_content = render_to_string('gimmo/pages/parametre/activekey.html', {'code':softk,'typeab':typeab,'etab':Etablissement.objects.get(id=Etablissement.objects.last().id)}) # render with dynamic value
        text_content = strip_tags(html_content) # Strip the html tag. So people can see the pure text at least.
        # create the email, and attach the HTML version as well.
        msg = EmailMultiAlternatives(subject, text_content, from_email, [to])
        msg.attach_alternative(html_content, "text/html")
        msg.send()
        etat = 1
        data = {
        'etat': etat,
        'montant': payvalue
        }

    return JsonResponse(data)

def cleactivation(request):
    etat = ""
    if request.method == 'POST':
        keyfile = request.POST['keyfile']
        #jour = date.today()
        #jour_expire = str(int(jour.day)+45)
        ########################################
    
        if Softkeyactive.objects.all().count() != 0:
            #print(end_date_soft) 
            end_date_soft = str(Softkeyactive.objects.last().datesoft)
            date_format_str = '%Y-%m-%d %H:%M:%S.%f'
            start = datetime.strptime(str(datetime.now()), date_format_str)
            end =   datetime.strptime(end_date_soft, date_format_str)
            # Get interval between two timstamps as timedelta object
            diff = end - start
            diff_in_hours = (diff.total_seconds() / 3600)
            diff_in_hours = diff_in_hours /24
            
            
            if diff_in_hours < 0.1:
                old_rest_date = int(round(diff_in_hours,1))
            else:
                old_rest_date = int(round(diff_in_hours,1))
        else:
            old_rest_date = 0

        ###########################################
        
        start_date = datetime.today()
        date_1 = pd.to_datetime(start_date)
        typeabon = 0
        t_key_count = Tempsoftkeyactive.objects.all().count()
        if t_key_count == 0:
            etat = "Clé d'activation incorrecte"
        else:
            t_key = Tempsoftkeyactive.objects.get(id=Tempsoftkeyactive.objects.last().id)
            if t_key.etat == 0:
                if t_key.keyword == keyfile:
                    key_count = Softkeyactive.objects.all().count()
                    end_date = date_1+pd.DateOffset(days=(t_key.typeab+old_rest_date))
                    if key_count == 0:
                        Softkeyactive.objects.create(
                            keyword = keyfile,
                            datesoft = end_date
                        ).save()
                    else:
                        Softkeyactive.objects.filter(id=Softkeyactive.objects.last().id).update(
                            keyword = keyfile,
                            datesoft = end_date
                        )
                    Tempsoftkeyactive.objects.filter(keyword=keyfile).update(
                        etat = 1
                    )
                    typeabon = t_key.typeab
                    etat = "1"
                    print(etat)
                else:
                    etat = "Clé d'activation incorrecte"
            else:
                etat = "Clé d'activation déjà utilisée"

        if typeabon == 31:
            typeabon_txt = '1 Mois'
        elif typeabon == 186:
            typeabon_txt = '6 Mois'
        elif typeabon == 365:
            typeabon_txt = '1 An'
        else:
            typeabon_txt = '5 Ans'
    
        data = {
        'etat':etat,
        'typeab':typeabon_txt
        }
    return JsonResponse(data)

def activationdone(request):
    etat = 0
    ########################################    
    #print(end_date_soft) 
    if Softkeyactive.objects.all().count() != 0:
        end_date_soft = str(Softkeyactive.objects.last().datesoft)
        date_format_str = '%Y-%m-%d %H:%M:%S.%f'
        start = datetime.strptime(str(datetime.now()), date_format_str)
        end =   datetime.strptime(end_date_soft, date_format_str)
        # Get interval between two timstamps as timedelta object
        diff = end - start
        diff_in_hours = (diff.total_seconds() / 3600)
        diff_in_hours = diff_in_hours /24
            
            
        if diff_in_hours < 0.1:
            old_rest_date = int(round(diff_in_hours,1))
        else:
            old_rest_date = int(round(diff_in_hours,1))
    else:
        old_rest_date = 0

    ###########################################
    start_date = datetime.today()
    date_1 = pd.to_datetime(start_date)

    t_key = Tempsoftkeyactive.objects.get(id=Tempsoftkeyactive.objects.last().id)
    keyfile = t_key.keyword
    key_count = Softkeyactive.objects.all().count()
    end_date = date_1+pd.DateOffset(days=(t_key.typeab+old_rest_date))
    if key_count == 0:
        Softkeyactive.objects.create(
            keyword = keyfile,
            datesoft = end_date
        ).save()
    else:
        Softkeyactive.objects.filter(id=Softkeyactive.objects.last().id).update(
            keyword = keyfile,
            datesoft = end_date
        )

    Tempsoftkeyactive.objects.filter(keyword=keyfile).update(
        etat = 1
    )

        


    typeabon = t_key.typeab
    etat = 1
    if typeabon == 31:
        typeabon_txt = '1 Mois'
    elif typeabon == 186:
        typeabon_txt = '6 Mois'
    elif typeabon == 370:
        typeabon_txt = '1 An'
    else:
        typeabon_txt = '5 Ans'
        
    data = {
    'etat':etat,
    'typeabon':typeabon_txt
    }

    return JsonResponse(data)

def error_404(request,exception):
    data = {}
    return render(request,'gimmo/error/404.html',data)


def error_500(request):
    data = {}
    return render(request,'gimmo/error/500.html',data)