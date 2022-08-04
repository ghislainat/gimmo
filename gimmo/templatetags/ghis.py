from datetime import date,datetime
from django import template
from django.template.defaultfilters import stringfilter
from gimmo.models import *
from django.conf import settings
import time,os
from django.db.models.query_utils import Q
from django.db.models import Count, F, Value, Avg, Max, Sum, Min, Subquery, OuterRef

register = template.Library()


@register.filter
def themevariable(value):
    if Themevar.objects.filter(user=value).exists():
        etat = Themevar.objects.get(user=value).etat
    else:
        etat = 0
    return etat

@register.filter
def getversion(value):
    return str(settings.GLINE_VERSION)


@register.filter
def strtointt(value):
    return int(value)

@register.filter
def strtoint(value):
    return str(value).replace(" ","")


@register.filter
def actifpro(value):
    value = Proprietaire.objects.filter(d1=1).count()
    return value


@register.filter
def getlocative(value):
    locative = Locative.objects.get(id=value).reflocative
    return locative

@register.filter
def inactifpro(value):
    value = Proprietaire.objects.filter(d1=0).count()
    return value

@register.filter
def allpro(value):
    value = Proprietaire.objects.all().count()
    return value

@register.filter
def actifloc(value):
    value = Locataire.objects.filter(d1=1).count()
    return value


@register.filter
def inactifloc(value):
    value = Locataire.objects.filter(d1=0).count()
    return value

@register.filter
def allloc(value):
    value = Locataire.objects.all().count()
    return value

@register.filter
def actifloca(value):
    value = Locative.objects.filter(etat=1).count()
    return value

@register.filter
def inactifloca(value):
    value = Locative.objects.filter(etat__gte=2).count()
    return value

@register.filter   
def alllocative(value):
    value = Locative.objects.filter(etat__gte=1).count()
    return value

@register.filter
def nombre_p_atten(value):
    facture_impmp = Facture.objects.filter(etat=3).count()
    return facture_impmp

@register.filter
def mois_passe(value):
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
    mois_passe = date.today().month - 1
    if mois_passe == 0:
        mois_passe = 12
    else:
        mois_passe = mois_passe

    mois_passe = tab_mois[mois_passe-1]
    
    return mois_passe


@register.filter
def facture_paye_mp(value):
    mois_passe = date.today().month - 1
    annee_courante = date.today().year
    if mois_passe == 0:
        mois_passe = 12
    else:
        mois_passe = mois_passe

    facture_payemp = Facture.objects.filter(creation__month=mois_passe,creation__year=annee_courante,etat=1).aggregate(tot=Sum('totfacture'))
    facture_payemp = facture_payemp['tot']
    if facture_payemp == None:
        facture_payemp = 0
    else:
        facture_payemp = facture_payemp

    return facture_payemp

@register.filter
def facture_impaye_mp(value):
    mois_passe = date.today().month - 1
    annee_courante = date.today().year
    if mois_passe == 0:
        mois_passe = 12
    else:
        mois_passe = mois_passe

    facture_impmp = Facture.objects.filter(Q(etat__gte=2)|Q(etat=0),creation__month=mois_passe,creation__year=annee_courante).aggregate(tot=Sum('totfacture'))
    facture_impmp = facture_impmp['tot']
    if facture_impmp == None:
        facture_impmp = 0
    else:
        facture_impmp = facture_impmp
    return facture_impmp

@register.filter
#@stringfilter
def nbbien(value):
    if Bien.objects.filter(proprietaire_id=value).exists():
        value = Bien.objects.filter(proprietaire_id=value).count()
    else:
        value = 0
    
    return value

@register.filter
def occuplocative(value):
    if Contrat.objects.filter(activecontrat__lte=1,locative_id=Locative.objects.get(id=int(value)).id).exists():
        #occupan = Contrat.objects.filter(activecontrat__lte=1,locative_id=Locative.objects.get(id=int(value)).id).count()
        #occupan = 'jj'+str(occupan)
        liste_contrat = Contrat.objects.filter(locative_id=Locative.objects.get(id=int(value)).id)
        for un_contrat in liste_contrat:
            if un_contrat.locative.etat == 2:
                occupant = str(un_contrat.locataire.nom.upper())+' '+str(un_contrat.locataire.prenom)
            elif un_contrat.locative.etat == 3:
                occupant = str(un_contrat.locataire.nom.upper())+' '+str(un_contrat.locataire.prenom)+'(Contrat inactif)'
            else:
                occupant = 'Vide'
    else:
        occupant = 'Vide'
    return occupant


@register.filter
def occuplocataire(value):
    occupant = ''
    if Contrat.objects.filter(locataire_id=Locataire.objects.get(id=int(value)).id,activecontrat__lte=1).exists():
        if Contrat.objects.filter(locataire_id=Locataire.objects.get(id=int(value)).id,activecontrat__lte=1).count() > 1:
            liste_locative = Contrat.objects.filter(locataire_id=Locataire.objects.get(id=int(value)).id)
            for une_locative in liste_locative:
                if une_locative.locative.etat != 0:
                    occupant += '&&'+str(une_locative.locative.reflocative)+'&&'
        else:
            un_contrat = Contrat.objects.get(locataire_id=Locataire.objects.get(id=int(value)).id,activecontrat__lte=1)
            if un_contrat.locative.etat == 2:
                occupant = str(un_contrat.locative.reflocative)
            elif un_contrat.locative.etat == 3:
                occupant = str(un_contrat.locative.reflocative)+'(Contrat inactif)'
            else:
                occupant = 'Vide'
    else:
        occupant = 'Vide'
    return occupant



@register.filter
def epargnemensuel(value):
    annee_encours = date.today().year

    facture_mois = Facture.objects.filter(etat=1,creation__month=int(value),creation__year=annee_encours).aggregate(tot=Sum('totfacture'))
    facture_mois = facture_mois['tot']
    if facture_mois == None:
        facture_mois = 0
    else:
        facture_mois = facture_mois
    
    depense_mois = Depense.objects.filter(creation__month=int(value),creation__year=annee_encours).aggregate(tot=Sum('valeur'))
    depense_mois = depense_mois['tot']
    if depense_mois == None:
        depense_mois = 0
    else:
        depense_mois = depense_mois

    value = facture_mois - depense_mois

    return str(value)