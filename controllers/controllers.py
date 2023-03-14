from odoo import http, _
import logging
import json
from odoo.http import HttpRequest, request, JsonRequest, Response
from odoo.tools import date_utils
import datetime
from werkzeug.exceptions import BadRequest

_logger = logging.getLogger(__name__)

def alternative_json_response(self, result=None, error=None):
  if error is not None:
      response = error
  if result is not None:
      response = result
  mime = 'application/json'
  body = json.dumps(response, default=date_utils.json_default)
  return Response(
    body, status=error and error.pop('http_status', 200) or 200,
    headers=[('Content-Type', mime), ('Content-Length', len(body))]
  )

class Odoo3cxCrm(http.Controller):
    @http.route('/api/3cx/crm', auth='public', csrf=False, type='json', methods=['POST'])
    def odoo_3cx_query (self, ** kw):
        now = datetime.datetime.now()
        str_now = str(now)
        data_string = str_now[:19]
        print("Data e ora: ", data_string)
        token = request.env.ref('3cxcrm.token_3cx_crm').sudo().value
        request._json_response = alternative_json_response.__get__(request, JsonRequest)
        data = json.loads(request.httprequest.data)
        apikey = request.httprequest.headers.get('apikey')
        activecalls = request.httprequest.headers.get('activecalls')
        callslist = request.httprequest.headers.get('callslist')
        print("activecalls: ", activecalls)
        print("callslist: ", callslist)

        number = str(data.get('number'))

        if apikey:
            if not apikey == token:
                return BadRequest('Wrong APIKEY')
            else:
                # cerco il numero sia tra i contatti che tra le opportunità
                res_partner = request.env['res.partner'].with_user(1).search([('phone_mobile_search','ilike', number)],limit=1)
                crm_lead = request.env['crm.lead'].with_user(1).search([('phone_mobile_search','ilike', number)],limit=1)

                # Vedo se il numero che ha chiamato corrisponde ad un contatto registrato in odoo
                partner_action_id = request.env.ref('contacts.action_contacts')
                crm_action_id = request.env.ref('crm.crm_lead_all_leads')

                # Se il numero che ha chiamato appartiene ad un contatto registrato su odoo raccolgo i dati
                if res_partner:
                    print("Data e ora: ", data_string)
                    print('res_partner', res_partner)
                    b = res_partner
                    link = f"web#id={b.id}&model=res.partner&view_type=form&action={partner_action_id.id}"
                    company = ""
                    if b.company_type == "company":
                        company = b.name
                    else:
                        company = ""
                    data={
                        'partner_id': f"{b.id}",
                        'type': b.type,
                        'firstname':  b.firstname if b.firstname else '',
                        'lastname': b.lastname if b.lastname  else '',
                        'mobile': b.mobile if b.mobile else '',
                        'phone': b.phone if b.phone else '',
                        'email': b.email if b.email else '',
                        'web_url': f"{request.httprequest.url_root}{link}",
                        'company_type': b.company_type if b.company_type == "company" else '',
                        'name': company,
                        'link_end': 'link_end'
                    }

                    nome_contatto = b.firstname + " " + b.lastname

                    # registro la chiamata nel registro delle chiamate
                    id_name = request.env['trecxcrm'].sudo().create({
                        'telefono': number,
                        'name': b.firstname,
                        'cognome': b.lastname,
                        'indirizzo_url': f"{request.httprequest.url_root}{link}",
                    }).id

                    # vedo se è presente un'opportunità corrispondente a quel numero e cliente registrato
                    crm_lead = request.env['crm.lead'].sudo().search([('phone_mobile_search', 'ilike', number)],limit=1)
                    print('crm_lead: ',crm_lead)

                    # se esite un'opportunità con il numero che ha chiamato leggo il suo stage_id
                    if crm_lead:
                        stage = crm_lead.stage_id
                        print('stage: ', int(stage))
                        # se l'opportunità è nella prima colonna non faccio niente altrimenti creo un'opportunità
                        if int(stage) != 1:
                            print('Il numero che ha chiamato corrisponde ad un contatto')
                            print("non c'è nessuna opportunità nella prima colonna")
                            print("Quindi creo un'opportunità da gestire (prima colonna)")
                            lead = request.env["crm.lead"].sudo().create({
                                "contact_name": nome_contatto,
                                "description": "Chiamata da 3CX",
                                "email_from": b.email,
                                "name": nome_contatto,
                                "partner_name": "Some company",
                                "team_id": '1',
                                "phone": number,
                                "ultima_chiamata": now,
                                "numero_chiamate": 1
                            })

                        # l'opportunità esiste ed è nella prima colonna quindi non faccio niente
                        else:
                            print("Il numero che ha chiamato appartiene ad un cliente registrato")
                            print("Esiste già un'opportunità nella prima colonna cioè non gestita")
                            print("Aggiorno il numero di chiamate nel nome dell'opportunità")
                            numero_chiamate = crm_lead['numero_chiamate']
                            print("numero_chiamate: ", numero_chiamate)
                            print("Quindi modifico il nome dell'opportunità esistente")
                            numero_chiamate = numero_chiamate + 1
                            crm_lead.write({
                                "numero_chiamate": numero_chiamate,
                                "ultima_chiamata": now
                            })
                            pass

                    # se non è nella prima colonna significa che l'opportunità è già in gestione
                    # allora aggiungo una nuova opportunità, con i dati completi del cliente letti da database
                    else:
                        print("Il numero che ha chiamato è di un cliente registrato")
                        print("non esiste nessuna opportunità nella prima colonna")
                        print("Quindi creo un'opportunita' da gestire (prima colonna)")
                        print("Data: ", now)
                        lead = request.env["crm.lead"].sudo().create({
                            "contact_name": nome_contatto,
                            "description": "Chiamata da 3CX",
                            "email_from": b.email,
                            "name": nome_contatto,
                            "partner_name": "Some company",
                            "team_id": '1',
                            "phone": number,
                            "ultima_chiamata": now,
                            "numero_chiamate": 1
                        })

                        print("Dopo la creazione del lead: ",crm_lead.id)

                    # ritorno i dati al 3cx
                    return data

                # Il numero che ha chiamato non appartiene a nessun cotatto registrato nel DB di odoo
                # prima di creare un'opportunità controllo che non ci sia già un'opportunità da gestire
                elif crm_lead:
                    print('crm_lead',crm_lead)
                    b = crm_lead
                    if b.type == 'lead':
                        link = f"web#id={b.id}&model=crm.lead&view_type=form&action={crm_action_id.id}"
                    elif b.type == 'opportunity':
                        link = f"web#id={b.id}&model=crm.lead&view_type=form&action={crm_action_id.id}"

                    # Leggo i dati del contato
                    data={
                        'partner_id': f"L{b.id}",
                        'type' : b.type,
                        'name' :  b.contact_name if b.contact_name else b.name,
                        'contact_name': b.name if b.name  else '',
                        'mobile': b.mobile if b.mobile else '',
                        'phone' : b.phone if b.phone else '',
                        'web_url': f"{request.httprequest.url_root}{link}",
                        'link_end': 'link_end'
                    }
                    # registro i dati nella lista delle chiamate
                    id_name = request.env['trecxcrm'].sudo().create({
                        'telefono': number,
                        'name': b.firstname,
                        'cognome': b.lastname,
                        'indirizzo_url': f"{request.httprequest.url_root}{link}",
                    }).id
                    # leggo lo stato dello stage_id
                    stage = b.stage_id
                    print('stage: ', int(stage))
                    # se l'opportunità esiste ed è nella prima colonna non faccio niente altrimenti creo un'opportunità
                    if int(stage) != 1:
                        lead = request.env["crm.lead"].sudo().create({
                            "contact_name": number,
                            "description": "Chiamata da 3CX",
                            "email_from": '',
                            "name": "Nuovo Contato: " + number,
                            "partner_name": "Some company",
                            "team_id": '1',
                            "phone": number,
                            "ultima_chiamata": now,
                            "numero_chiamate": 1
                        })
                        # registro la chiamata nel registro delle chiamate
                        id_name = request.env['trecxcrm'].sudo().create({
                            'telefono': number,
                            'name': 'Nuovo Contatto',
                        }).id

                    # non esiste nessun crm_lead
                    else:
                        # 2) questo viene eseguito quando il cliente non è registrato ma c'è già un'opportunità da gestire con
                        # lo stesso numero
                        print("Esiste un crm_lead")
                        print("Il numero chiamante non è registrato nel DB di odoo")
                        print("Ma c'è già 'opportunità presente nella prima colonna con numero: ", number)
                        numero_chiamate = crm_lead['numero_chiamate']
                        print("numero_chiamate: ", numero_chiamate)
                        print("Quindi modifico il nome dell'opportunità esistente")
                        numero_chiamate = numero_chiamate + 1
                        crm_lead.write({
                            "numero_chiamate": numero_chiamate,
                            "ultima_chiamata": now
                        })
                        pass

                    # ritorno i dati al 3cx
                    return data

                else:
                    print("Il numero chiamante non appartiene a nessun cliente registrato")
                    print("non esiste nessuna opportunità nella prima colonna")
                    print("Quindi creo un'opportunità da gestire")
                    print("Data: ", now)
                    lead = request.env["crm.lead"].sudo().create({
                        "contact_name": number,
                        "description": "Chiamata da 3CX",
                        "email_from": '',
                        "name": "Nuovo Contato: "  + number,
                        "partner_name": "Some company",
                        "team_id": '1',
                        "phone": number,
                        "ultima_chiamata": now,
                        "numero_chiamate": 1
                    })
                    # registro i dati nella lista delle chiamate
                    id_name = request.env['trecxcrm'].sudo().create({
                        'telefono': number,
                        'name': 'Nuovo Contatto',
                    }).id

                    data = {"new_number": True}
                    return data

        return BadRequest('ApiKey not set')

class Odoo3cxCalls(http.Controller):
    @http.route('/api/3cx/calls', auth='public', csrf=False, type='json', methods=['POST'])
    def odoo_3cx_query (self, ** kw):
        token = request.env.ref('3cxcrm.token_3cx_crm').sudo().value
        request._json_response = alternative_json_response.__get__(request, JsonRequest)
        data = json.loads(request.httprequest.data)
        apikey = request.httprequest.headers.get('apikey')

        number = str(data.get('number'))
        nome_operatore = str(data.get('nome_operatore'))
        data_inizio = str(data.get('data_inizio'))
        data_fine = str(data.get('data_fine'))
        token_call = str(data.get('token_call'))

        # print("number:", number)
        # print("nome_operatore:", nome_operatore)
        # print("data_inizio:", data_inizio)
        # print("data_fine:", data_fine)
        # print("token_call:", token_call)

        if apikey:
            if not apikey == token:
                return BadRequest('Wrong APIKEY')
            else:
                res_partner = request.env['res.partner'].with_user(1).search([('phone_mobile_search','ilike', number)],limit=1)
                crm_lead = request.env['crm.lead'].with_user(1).search([('phone_mobile_search','ilike', number)],limit=1)
                token_presence = request.env['trecxcrm'].with_user(1).search([('token_call', '=', token_call )], limit=1)

                # Vedo se il numero che ha chiamato corrisponde ad un contatto registrato in odoo
                partner_action_id = request.env.ref('contacts.action_contacts')
                crm_action_id = request.env.ref('crm.crm_lead_all_leads')

                # Se il numero che ha chiamato appartiene ad un contatto registrato su odoo raccolgo i dati
                if res_partner:
                    print('res_partner', res_partner)
                    b = res_partner
                    link = f"web#id={b.id}&model=res.partner&view_type=form&action={partner_action_id.id}"
                    company = ""
                    if b.company_type == "company":
                        company = b.name
                    else:
                        company = ""
                    data={
                        'partner_id': f"{b.id}",
                        'type': b.type,
                        'firstname':  b.firstname if b.firstname else '',
                        'lastname': b.lastname if b.lastname  else '',
                        'mobile': b.mobile if b.mobile else '',
                        'phone': b.phone if b.phone else '',
                        'email': b.email if b.email else '',
                        'web_url': f"{request.httprequest.url_root}{link}",
                        'company_type': b.company_type if b.company_type == "company" else '',
                        'name': company,
                        'link_end': 'link_end'
                    }

                    # Scrivo i dati nella lista delle chiamate
                    if not token_presence:
                        print("number:", number)
                        print("nome_operatore:", nome_operatore)
                        print("data_inizio:", data_inizio)
                        print("data_fine:", data_fine)
                        print("token_call:", token_call)
                        id_name = request.env['trecxcrm'].sudo().create({
                            'operatore': nome_operatore,
                            'data_inizio': data_inizio,
                            'data_fine': data_fine,
                            'telefono': number,
                            'name': b.firstname,
                            'cognome': b.lastname,
                            'indirizzo_url': f"{request.httprequest.url_root}{link}",
                            'token_call': token_call,
                        }).id
                    else:
                        print("Token già esistente")

                    if crm_lead:
                        print('Il numero che ha chiamato corrisponde ad un contatto')

                    # ritorno i dati al 3cx
                    return data

                else:
                    if not token_presence:
                        print("number:", number)
                        print("nome_operatore:", nome_operatore)
                        print("data_inizio:", data_inizio)
                        print("data_fine:", data_fine)
                        print("token_call:", token_call)
                        # Scrivo i dati nella lista delle chiamate
                        id_name = request.env['trecxcrm'].sudo().create({
                            'operatore': nome_operatore,
                            'data_inizio': data_inizio,
                            'data_fine': data_fine,
                            'telefono': number,
                            'name': 'Nuovo Contatto',
                            'token_call': token_call,
                        }).id
                    else:
                        print("Token già esistente")


                    data = {"new_number": True}
                    return data

        return BadRequest('ApiKey not set')

class Odoo3cxRealtime(http.Controller):
    @http.route('/api/3cx/realtime', auth='public', csrf=False, type='json', methods=['POST'])
    def odoo_3cx_query (self, ** kw):
        import re
        token = request.env.ref('3cxcrm.token_3cx_crm').sudo().value
        request._json_response = alternative_json_response.__get__(request, JsonRequest)
        data = json.loads(request.httprequest.data)
        apikey = request.httprequest.headers.get('apikey')

        if apikey:
            if not apikey == token:
                return BadRequest('Wrong APIKEY')
            else:
                dati_ricevuti = data.get('data')
                #print("Lunghezza array:", dati_ricevuti)

                calls_to_remove = request.env['trecx_realtime'].with_user(1).search([('checksum', '!=', 'checksum')])
                print("calls_to_remove", calls_to_remove)
                calls_to_remove.sudo().unlink()


                persone = []

                for dati in dati_ricevuti:
                    persona = {}
                    for i, (k, v) in enumerate(dati.items()):
                        if i < 5:
                            persona[k] = v
                        else:
                            break
                    persone.append(persona)
                    print("Persona", persona)
                    valore_checksum = persona['checksum']
                    print("checksum:",valore_checksum)
                    record = request.env['trecx_realtime'].sudo().create(persona).id
                print(persone)


                    # record = request.env['trecx_realtime'].sudo().create(dizionario).id


                # Inserimento dei record nel database
                # for record in array:
                #     print(record)
                #
                #
                #
                #
                # # calls = request.env['trecx_realtime'].with_user(1).search([('checksum', '=', checksum)])
                # # if calls:
                # #     calls.write({'durata': durata})
                # #     print("Questa chiamata non esiste quindi la inserisco")
                #     io ho questi dati:  [Talking; Anna Maria Lunghi; 3336018942; 16 min;6a5957b9253c95670ae7b9452e39b43218e428c8f1171eafdd894a06cc924f1c;Talking;Maurizio Aquino;3336018942;16 min;d1ab6166ac2c7b7b1625eef46e9a7373f37c10d2ef3f7925688466146211c4c3]
                #     vorrei convertirli in modo da salvare il record di odoo15 come sotto riportato, , scrivi il codice python per fare questo
                #     record = request.env['trecx_realtime'].sudo().create({
                #         'stato': stato,
                #         'chiamante': chiamante,
                #         'chiamato': chiamato,
                #         'durata': durata,
                #         'checksum': checksum,
                #     }).id
                #     print("Ho inserito i dati della chiamata")
                # else:
                #     calls_to_remove = request.env['trecx_realtime'].with_user(1).search([('checksum', '!=', checksum)])
                #     calls_to_remove.sudo().unlink()


                # print("Poi rimuovo tutti i record che non contengono il checksum:", checksum)
                # calls_to_remove = request.env['trecx_realtime'].with_user(1).search([('checksum', '!=', 'checksum')])
                # print("I record che non contengono il checksum: ", checksum)
                # print("sono: ", calls_to_remove)
                # calls_to_remove.sudo().unlink()
                # print("stato: ", stato)
                # print("chiamante: ", chiamante)
                # print("chiamato: ", chiamato)
                # print("durata: ", durata)
                # print("checksum: ", checksum)
                # print("################################################")
                #
                # print("cerco il record che contiene il checksum",checksum)
                # print("Il record che contiene il checksum:", checksum)
                # call_found = request.env['trecx_realtime'].with_user(1).search([('checksum', '=', checksum)])
                # print("è questo:", call_found)



                # if call_found:
                #     print("Modifico la chiamata già presente")
                #     call_found.write({
                #         "durata": durata,
                #     })
                # else:
                #     print("Questa chiamata non esiste quindi la inserisco")
                #     id_name = request.env['trecx_realtime'].sudo().create({
                #         'stato': stato,
                #         'chiamante': chiamante,
                #         'chiamato': chiamato,
                #         'durata': durata,
                #         'checksum': checksum,
                #     }).id
                # print("Ho inserito i dati della chiamata")
                return True

        return BadRequest('ApiKey not set')
