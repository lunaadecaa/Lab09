from database import punto_interesse_DAO
from database.parco_DAO import ParcoDAO
from database.escursione_DAO import EscursioneDAO
from database.punto_interesse_DAO import PuntoInteresseDAO

class Model:
    def __init__(self):
        self.escursioni_map = {} # Mappa ID escursione -> oggetti Escursione
        self.punti_interesse_map = {} # Mappa ID punto di interesse -> oggetti PuntoInteresse

        self._pacchetto_ottimo = []
        self._valore_ottimo: int = -1
        self._costo:float = 0
        self._gg =None
        self.max_budget =None



        # Caricamento
        self.load_parchi()
        self.load_escursioni()
        self.load_punti_interesse()
        self.load_relazioni()

    @staticmethod
    def load_parchi():
        """ Restituisce tutti i parchi disponibili """
        return ParcoDAO.get_parchi()

    def load_escursioni(self):
        """ Carica tutte le escursioni in un dizionario [id, Escursione]"""
        self.escursioni_map = EscursioneDAO.get_escursioni()

    def load_punti_interesse(self):
        """ Carica tutti i punti di interesse in un dizionario [id, PuntoInteresse]"""
        self.punti_interesse_map = PuntoInteresseDAO.get_punti_interesse()

    def load_relazioni(self):
        """
            Interroga il database per ottenere tutte le relazioni fra escursioni e punti di interesse e salvarle nelle strutture dati
            Collega escursione <-> punti di interesse.
            --> Ogni Escursione ha un set di PuntoInteresse.
            --> Ogni PuntoInteresse ha un set di Escursioni.

        """
        escursione=EscursioneDAO.get_escursioni_punti_interesse()
        for es in escursione:

            id_esc, id_pi = es["id_escursione"], es["id_punto_interesse"]

            esc = self.escursioni_map.get(id_esc)
            pi = self.punti_interesse_map.get(id_pi)

            if esc is not None and pi is not None:
                esc.punti_interesse.add(pi)  # set di PuntoInteresse dentro Escursione
                pi.escursioni.add(esc)  # set di Escursione dentro PuntoInteresse
        #fine non serve il return, essendoci add aggoornera direttamente il self senza bisogno di fare un return

    def genera_pacchetto(self, id_parco: str, max_giorni: int = None, max_budget: float = None):
        """
        Calcola il pacchetto di escursioni ottimale per un parco rispettando i vincoli di durata, budget e punti di interesse unici.
        :param id_parco: id del parco
        :param max_giorni: numero massimo di giorni (può essere None --> nessun limite)
        :param max_budget: costo massimo del pacchetto (può essere None --> nessun limite)


        """
        self._pacchetto_ottimo = []


        self._gg= max_giorni
        self._max_budget=max_budget

        escursioni=[]
        for es in self.escursioni_map.values():
            if es.id_parco==id_parco:
                escursioni.append(es)

        self._ricorsione(0,[],0,self._costo,self._valore_ottimo,set(),self._gg,self._max_budget,escursioni)

        self._costo = sum(esc.costo for esc in self._pacchetto_ottimo)

        """
        :return: self._pacchetto_ottimo (una lista di oggetti Escursione)
        :return: self._costo (il costo del pacchetto)
        :return: self._valore_ottimo (il voto complessivo dei visitatori per il pacchetto)"""

        return self._pacchetto_ottimo, self._costo, self._valore_ottimo

    def _ricorsione(self, start_index: int, pacchetto_parziale: list, durata_corrente: int, costo_corrente: float,
                    valore_corrente: int, punti_usati: set, gg_max:float,budget_max:float,escursioni):
        """Algoritmo di ricorsione che massimizza la somma dei voti dei punti di interesse."""
        if valore_corrente > self._valore_ottimo:
            self._valore_ottimo = valore_corrente
            self._pacchetto_ottimo = list(pacchetto_parziale)

        for i in range(start_index, len(escursioni)):
            esc = escursioni[i]

            nuova_durata = durata_corrente + esc.durata_giorni
            nuovo_costo = costo_corrente + float(esc.costo)

            if gg_max is not None and nuova_durata > gg_max:
                continue
            if budget_max is not None and nuovo_costo > budget_max:
                continue
            if esc.punti_interesse & punti_usati:
                continue

            nuovi_punti = esc.punti_interesse - punti_usati
            valore_aggiunto = sum(pi.voto_visitatori for pi in nuovi_punti)

            pacchetto_parziale.append(esc)
            punti_usati.update(nuovi_punti)

            self._ricorsione(
                start_index=i + 1,
                pacchetto_parziale=pacchetto_parziale,
                durata_corrente=nuova_durata,
                costo_corrente=nuovo_costo,
                valore_corrente=valore_corrente + valore_aggiunto,
                punti_usati=punti_usati,
                gg_max=gg_max,
                budget_max=budget_max,
                escursioni=escursioni,
            )

            pacchetto_parziale.pop()
            punti_usati.difference_update(nuovi_punti)
        return self._valore_ottimo, self._pacchetto_ottimo
