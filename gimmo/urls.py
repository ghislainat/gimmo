from django.views.static import serve

from django.urls import path, include
from django.contrib import admin

from django.conf.urls.static import static
from django.conf import settings
#from django.contrib.auth import views as auth_views
from . import views as as_views
#jsvdtog1
#0IGmQ4s-1mf(4S
from django.contrib.auth.views import *

urlpatterns = [
  #url(r'^media/(?P<path>.*)$', serve,{'document_root': settings.MEDIA_ROOT}),
  #url(r'^static/(?P<path>.*)$', serve,{'document_root': settings.STATIC_ROOT}),
  #path('tinymce/', include('tinymce.urls')),
  path('', as_views.gimmo, name="gimmo"),
  path('accueil/', as_views.accueil, name="accueil"),
  path('deconnexion/', as_views.deconnexion, name="deconnexion"),
  #EMPLOYE
  path('employe/', as_views.employe, name="employe"),
  path('newemploye/', as_views.newemploye, name="newemploye"),
  path('eemploye/<str:pk>/', as_views.eemploye, name="eemploye"),
  path('ajxemp/', as_views.ajxemp, name="ajxemp"),
  path('eajxemp/', as_views.eajxemp, name="eajxemp"),
  path('infoEmploye/', as_views.infoEmploye, name="infoEmploye"),
  path('pdfemploye/', as_views.pdfemploye, name="pdfemploye"),
  path('pdfunemploye/<str:pk>/', as_views.pdfunemploye, name="pdfunemploye"),
  #PROPRIETAIRE
  path('proprietaire/', as_views.proprietaire, name="proprietaire"),
  path('lproprietaire/<str:pk>/', as_views.lproprietaire, name="lproprietaire"),
  path('pdfrapportproprietaire/<str:pk>/', as_views.pdfrapportproprietaire, name="pdfrapportproprietaire"),
  path('newproprietaire/', as_views.newproprietaire, name="newproprietaire"),
  path('eproprietaire/<str:pk>/', as_views.eproprietaire, name="eproprietaire"),
  path('ajxpro/', as_views.ajxpro, name="ajxpro"),
  path('eajxpro/', as_views.eajxpro, name="eajxpro"),
  path('infoProprietaire/', as_views.infoProprietaire, name="infoProprietaire"),
  path('desProprietaire/', as_views.desProprietaire, name="desProprietaire"),
  path('delProprietaire/', as_views.delProprietaire, name="delProprietaire"),
  path('pdfproprietaire/', as_views.pdfproprietaire, name="pdfproprietaire"),
  path('pdfunproprietaire/<str:pk>/', as_views.pdfunproprietaire, name="pdfunproprietaire"),
  #LOCATAIRE
  path('locataire/', as_views.locataire, name="locataire"),
  path('llocataire/<str:pk>/', as_views.llocataire, name="llocataire"),
  path('pdfrapportlocataire/<str:pk>/', as_views.pdfrapportlocataire, name="pdfrapportlocataire"),
  path('newlocataire/', as_views.newlocataire, name="newlocataire"),
  path('elocataire/<str:pk>/', as_views.elocataire, name="elocataire"),
  path('ajxloc/', as_views.ajxloc, name="ajxloc"),
  path('eajxloc/', as_views.eajxloc, name="eajxloc"),
  path('infoLocataire/', as_views.infoLocataire, name="infoLocataire"),
  path('desLocataire/', as_views.desLocataire, name="desLocataire"),
  path('delLocataire/', as_views.delLocataire, name="delLocataire"),
  path('pdflocataire/', as_views.pdflocataire, name="pdflocataire"),
  path('pdfunlocataire/<str:pk>/', as_views.pdfunlocataire, name="pdfunlocataire"),
  #LOCATIVE
  path('locative/', as_views.locative, name="locative"),
  path('newlocative/', as_views.newlocative, name="newlocative"),
  path('elocative/<str:pk>/', as_views.elocative, name="elocative"),
  path('ajxlocative/', as_views.ajxlocative, name="ajxlocative"),
  path('eajxlocative/', as_views.eajxlocative, name="eajxlocative"),
  path('infoLocative/', as_views.infoLocative, name="infoLocative"),
  path('desLocative/', as_views.desLocative, name="desLocative"),
  path('delLocative/', as_views.delLocative, name="delLocative"),
  path('pdflocative/', as_views.pdflocative, name="pdflocative"),
  path('pdfunelocative/<str:pk>/', as_views.pdfunelocative, name="pdfunelocative"),
  #BIEN
  path('bien/', as_views.bien, name="bien"),
  path('newbien/', as_views.newbien, name="newbien"),
  path('ebien/<str:pk>/', as_views.ebien, name="ebien"),
  path('ajxbien/', as_views.ajxbien, name="ajxbien"),
  path('eajxbien/', as_views.eajxbien, name="eajxbien"),
  path('infoBien/', as_views.infoBien, name="infoBien"),
  path('desBien/', as_views.desBien, name="desBien"),
  path('delBien/', as_views.delBien, name="delBien"),
  path('pdfbien/', as_views.pdfbien, name="pdfbien"),
  path('pdfunbien/<str:pk>/', as_views.pdfunbien, name="pdfunbien"),
  #DEPENSE
  path('depense/', as_views.depense, name="depense"),
  path('newdepense/', as_views.newdepense, name="newdepense"),
  path('edepense/<str:pk>/', as_views.edepense, name="edepense"),
  path('ajxdepense/', as_views.ajxdepense, name="ajxdepense"),
  path('eajxdepense/', as_views.eajxdepense, name="eajxdepense"),
  path('desdepense/', as_views.desdepense, name="desdepense"),
  path('deldepense/', as_views.deldepense, name="deldepense"),
  path('pdfdepense/', as_views.pdfdepense, name="pdfdepense"),
  path('pdfunedepense/<str:pk>/', as_views.pdfunedepense, name="pdfunedepense"),
  #CONTRAT
  path('contrat/', as_views.contrat, name="contrat"),
  path('newcontrat/', as_views.newcontrat, name="newcontrat"),
  path('econtrat/<str:pk>/', as_views.econtrat, name="econtrat"),
  path('ajxcontrat/', as_views.ajxcontrat, name="ajxcontrat"),
  path('eajxcontrat/', as_views.eajxcontrat, name="eajxcontrat"),
  path('bienproprietaire/', as_views.bienproprietaire, name="bienproprietaire"),
  path('locativeproprietaire/', as_views.locativeproprietaire, name="locativeproprietaire"),
  path('selectedlocative/', as_views.selectedlocative, name="selectedlocative"),
  path('infoContrat/', as_views.infoContrat, name="infoContrat"),
  path('closeContrat/', as_views.closeContrat, name="closeContrat"),
  path('delContrat/', as_views.delContrat, name="delContrat"),
  path('pdfcontrat/', as_views.pdfcontrat, name="pdfcontrat"),
  path('pdfuncontrat/<str:pk>/', as_views.pdfuncontrat, name="pdfuncontrat"),
  #PAIEMENT
  path('paiement/', as_views.paiement, name="paiement"),
  path('payer/', as_views.payer, name="payer"),
  path('payinfo/', as_views.payinfo, name="payinfo"),
  path('payerloyer/', as_views.payerloyer, name="payerloyer"),
  path('facture/<str:pk>/', as_views.facture, name="facture"),
  path('exporterfac/<str:pk>/', as_views.exporterfac, name="exporterfac"),
  path('exporterrec/<str:pk>/', as_views.exporterrec, name="exporterrec"),
  path('exporterunefac/<str:pk>/', as_views.exporterunefac, name="exporterunefac"),
  path('ajxfacture/', as_views.ajxfacture, name="ajxfacture"),
  path('rapport/', as_views.rapport, name="rapport"),
  path('detailPaiem/', as_views.detailPaiem, name="detailPaiem"),
  path('pdfpaiement/', as_views.pdfpaiement, name="pdfpaiement"),
  path('pdfrapport/', as_views.pdfrapport, name="pdfrapport"),
  #PAIEMENT A VENIR
  path('paiementav/', as_views.paiementav, name="paiementav"),
  #PARAMETRE
  path('fichier/', as_views.fichier, name="fichier"),
  path('ajxfichier/', as_views.ajxfichier, name="ajxfichier"),
  path('downfichier/<str:pk>/', as_views.downfichier, name="downfichier"),
  #MESSAGE
  path('message/', as_views.message, name="message"),
  path('get_sms_user/', as_views.get_sms_user, name="get_sms_user"),
  #PARAMETRE
  path('parametre/', as_views.parametre, name="parametre"),
  path('ajxetab/', as_views.ajxetab, name="ajxetab"),
  path('ajxetabconfig/', as_views.ajxetabconfig, name="ajxetabconfig"),
  path('profile/', as_views.profile, name="profile"),
  path('infoprofile/<str:pk>/', as_views.infoprofile, name="infoprofile"),
  path('themevar/', as_views.themevar, name="themevar"),
  path('updatemdp/', as_views.updatemdp, name="updatemdp"),
  #PAIEMENT
  path('pay/', as_views.pay, name="pay"),
  path('abonnementtab/', as_views.abonnementtab, name="abonnementtab"),
  path('typeabonnement/', as_views.typeabonnement, name="typeabonnement"),
  path('demandeactivation/', as_views.demandeactivation, name="demandeactivation"),
  path('cleactivation/', as_views.cleactivation, name="cleactivation"),
  path('activationdone/', as_views.activationdone, name="activationdone"),
  #path('index/', as_views.index, name="index"),
  path('i18n/', include('django.conf.urls.i18n')),
]