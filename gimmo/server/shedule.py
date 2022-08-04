import datetime
from datetime import *
import uuid
from django.conf import settings
import pandas as pd
from gimmo.models import *
from gimmo.views import senEmail


def shedule_api():
    #AUTO LOYER
    marge_paiement = -(Etablissement.objects.get(id=Etablissement.objects.last().id).margepay)
    annee_encours = date.today().year
    mois_encours = int(date.today().month)-1
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
    
    print('Begin')
    list_contrat = Contrat.objects.filter(activecontrat=1,prochainpay__month=date.today().month,prochainpay__year=annee_encours)
    for un_contrat in list_contrat:
        une_locative = un_contrat.locative.montant
        frais_sur_une_locative = un_contrat.locative.charge
        loyer = une_locative + frais_sur_une_locative
        limit_pay = un_contrat.limite

        date_pay = un_contrat.prochainpay
        date_pay_sd = pd.to_datetime(date_pay)
        end_date = date_pay_sd+pd.DateOffset(days=0)

        comparaison_date = end_date-datetime.now()
        diff_in_hours = (comparaison_date.total_seconds() / 3600)
        diff_in_days = (round((diff_in_hours /24),1))

        print('end_date-datetime.now()',diff_in_days)

        count_tab_facture = Facture.objects.all().count()
        idpub_facture = uuid.uuid4()
        idpub_facture = str(idpub_facture).replace("-","")
        publicid_facture = idpub_facture + str(count_tab_facture)
        ref_facture = 'FT26-'+str(count_tab_facture)
        typefacture = un_contrat.prochainpay#'Loyer du '+str(un_contrat.limite)+' '+str(tab_mois[mois_encours])



        #verifier si la facture est payee sinon envoi de mail
        if Facture.objects.filter(reffacture = ref_facture,etat=1).exists():
            print("Fature paye")

        elif Facture.objects.filter(reffacture = ref_facture,etat=2).exists():
            senEmail(typefacture,un_contrat,2,ref_facture)
            print("Fature en retard")
        else:

            if not Facture.objects.filter(locataire_id=un_contrat.locataire.id,creation__month=date.today().month,creation__year=annee_encours,typefacture=un_contrat.prochainpay).exists() and 1 <= diff_in_days <= 1.9 :
                if not Facture.objects.filter(reffacture = ref_facture).exists():
                    Facture.objects.create(
                        idpub = publicid_facture,
                        reffacture = ref_facture,
                        typefacture = typefacture,
                        dureepay = 1,
                        debutpay = None,
                        finpay = None,
                        totfacture = loyer,
                        payefacture = 0,
                        restefacture = loyer,
                        retardfacture = 0,
                        finaltotal = loyer,
                        etat = 3,
                        locataire = Locataire.objects.get(id=int(un_contrat.locataire.id)),
                        locative = Locative.objects.get(id=int(un_contrat.locative.id)),
                        contrat = Contrat.objects.get(refcontrat=un_contrat.refcontrat),
                        creation = datetime.now()
                    ).save()
                    senEmail(typefacture,un_contrat,0,ref_facture)
                    print('MISE EN GARDE')
                
                #MISE EN GARDE
            elif not Facture.objects.filter(locataire_id=un_contrat.locataire.id,creation__month=date.today().month,creation__year=annee_encours,typefacture=un_contrat.prochainpay).exists() and 0 <= diff_in_days <= 0.9:
                if not Facture.objects.filter(reffacture = ref_facture).exists():
                    Facture.objects.create(
                        idpub = publicid_facture,
                        reffacture = ref_facture,
                        typefacture = typefacture,
                        dureepay = 1,
                        debutpay = None,
                        finpay = None,
                        totfacture = loyer,
                        payefacture = 0,
                        restefacture = loyer,
                        retardfacture = 0,
                        finaltotal = loyer,
                        etat = 3,
                        locataire = Locataire.objects.get(id=int(un_contrat.locataire.id)),
                        locative = Locative.objects.get(id=int(un_contrat.locative.id)),
                        contrat = Contrat.objects.get(refcontrat=un_contrat.refcontrat),
                        creation = datetime.now()
                    ).save()
                    senEmail(typefacture,un_contrat,0,ref_facture)
                    print('JOUR PAIEMENT')

            else:
                #MESSAGE VEILLE
                if diff_in_days < 0:
                    #MESSAGE JOUR J Y
                    print('MESSAGE JOUR J Y +1')
                    senEmail(typefacture,un_contrat,1,ref_facture)

                elif diff_in_days < marge_paiement:
                    per_retard_loy = (un_contrat.locative.montant*un_contrat.retard)/100

                    #MESSAGE RETARD
                    if not Facture.objects.filter(reffacture = ref_facture,etat = 2).exists():
                        Facture.objects.filter(reffacture=ref_facture).update(
                            retardfacture = per_retard_loy,
                            finaltotal = (loyer+per_retard_loy),
                            etat = 2
                        )
                        senEmail(typefacture,un_contrat,2,ref_facture)
                        print('MESSAGE RETARDdddd')
                else:
                    #FACTURE NON GENERE
                    print('FACTURE NON GENERE')
            
shedule_api()