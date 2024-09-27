# -*- coding: utf-8 -*-
"""
  models.py
  Author : Jacek 'Szumak' Kotlarski --<szumak@virthost.pl>
  Created: 23.08.2024, 12:54:16
  
  Purpose: reports model classes.
"""

from typing import Optional, List, Tuple, Any
from threading import Event, Thread
from inspect import currentframe
from queue import Queue, Empty

from sqlalchemy import ForeignKey, Integer, Boolean, String, func, text, and_, true
from sqlalchemy.orm import Mapped, mapped_column, Query, relationship, aliased
from sqlalchemy.orm import Session

from jsktoolbox.attribtool import ReadOnlyClass
from jsktoolbox.logstool.logs import (
    LoggerClient,
    LoggerQueue,
)

from jsktoolbox.basetool.threads import ThBaseObject
from jsktoolbox.netaddresstool.ipv4 import Address, Network
from jsktoolbox.raisetool import Raise
from jsktoolbox.datetool import DateTime
from jsktoolbox.datetool import Timestamp
from jsktoolbox.stringtool.crypto import SimpleCrypto

from uke_pit2.base import BReportObject

from uke_pit2.db_models.reports import (
    LmsDivision,
    Division,
    LmsNetNode,
    Foreign,
    LmsAddress,
)


class RNode(BReportObject):
    """Node report class."""

    class Keys(object, metaclass=ReadOnlyClass):
        """Internal keys class."""

        ADDRESS: str = "__address__"
        IDENT: str = "__ident__"
        MAIN: str = "__main__"
        NODE: str = "__node__"

    def __init__(
        self,
        session: Session,
        logger_queue: LoggerQueue,
        node: LmsNetNode,
        main: bool,
        foreign_ident: str,
        verbose: bool,
        debug: bool,
    ) -> None:
        """Constructor."""

        self.logs = LoggerClient(logger_queue, self._c_name)
        self.debug = debug
        self.verbose = verbose
        self.session = session

        # set node
        self._set_data(key=RNode.Keys.NODE, set_default_type=LmsNetNode, value=node)

        # set main
        self._set_data(key=RNode.Keys.MAIN, set_default_type=bool, value=main)

        # set ident
        self._set_data(key=RNode.Keys.IDENT, set_default_type=str, value=foreign_ident)

        # set address

    def __address_update(self) -> None:
        """Get address record."""

        row = self.session.query(LmsAddress)

    @property
    def foreign_ident(self) -> str:
        """Returns foreign ident string."""
        return self._get_data(
            key=RNode.Keys.IDENT, set_default_type=str, default_value=""
        )  # type: ignore

    @property
    def main(self) -> bool:
        """Returns True if division is the main division."""
        return self._get_data(key=RNode.Keys.MAIN)  # type: ignore

    @property
    def rep_node(self) -> str:
        """Return cvs formatted string.

        Format:
        0. ident: String(100) # identyfikator węzła
        1. *owner: Dict[String] # tytuł własności węzła
        2. *owner_id: String(100) # identyfikator właściciela w przypadku dzierżawy
        3. *terc: Numeric(7) # identyfikator TERC
        4. *simc: Numeric(7) # identyfikator SIMC
        5. *ulic: Optional[Numeric(5)] # identyfikator ULIC
        6. *nr: Optional[String(50)] # adresowy numer porządkowy
        7. *latitude: Float(7) # szerokość geograficzna
        8. *longitude: Float(7) # długość geograficzna
        9. *medium: Dict[String] # medium transmisyjne 'słownik 3'
        10. bsa: Dict[Boolean] # możliwość świadczenia usług BSA
        11. access: Optional[Dict[String]] # lista technologii dostępowych 'słowniki: 1,2'
        12. services: Optional[Dict[String]] # lista usług transmisji danych 'słownik 6'
        13. if_add: Dict[Boolean] # możliwość zwiększania liczby interfejsów
        14. *financing: Dict[Boolean] # finansowanie ze środków publicznych
        15. *pnrs: Optional[String(250)] # numery projektów dla środków publicznych
        16. major: Dict[Boolean] # infrastruktura o dużym znaczeniu
        17. if_type: Optional[Dict[String]] # lista identyfikatorów typu interfejsu eth 'słownik 10'
        18. if_share: Optional[Dict[Boolean]] # możliwość udostępniania interfejsu eth
        """
        prefix: str = "WW_"  # węzeł własny/węzeł współdzielony
        owner: str = (
            "Węzeł własny" if self.main else "Węzeł współdzielony z innym podmiotem"
        )
        template = (
            "{ident:.100},"
            "{owner},"
            "{owner_id:.100},"
            "{terc:.7},"
            "{simc:.7},"
            "{ulic:.5},"
            "{nr:.50},"
            "{lat:.7},"
            "{lon:.7},"
            "{medium},"
            "{bsa:.3},"
            "{access},"
            "{services},"
            "{if_add:.3},"
            "{financing:.3},"
            "{pnrs},"
            "{major:.3},"
            "{if_type},"
            "{if_share}"
        )
        out: str = (
            f"{prefix}{self.__node.name},"  # "we01_id_wezla,"
            f"{owner},"  # "we02_tytul_do_wezla,"
            f"{self.foreign_ident},"  # "we03_id_podmiotu_obcego,"
            # "we04_terc,"
            # "we05_simc,"
            # "we06_ulic,"
            # "we07_nr_porzadkowy,"
            # "we08_szerokosc,"
            # "we09_dlugosc,"
            # "we10_medium_transmisyjne,"
            # "we11_bsa,"
            # "we12_technologia_dostepowa,"
            # "we13_uslugi_transmisji_danych,"
            # "we14_mozliwosc_zwiekszenia_liczby_interfejsow,"
            # "we15_finansowanie_publ,"
            # "we16_numery_projektow_publ,"
            # "we17_infrastruktura_o_duzym_znaczeniu,"
            # "we18_typ_interfejsu,"
            # "we19_udostepnianie_ethernet"
        )
        return template.format(
            ident=f"{prefix}{self.__node.name}",
            owner=owner,
            owner_id=self.foreign_ident,
        )

    @property
    def __node(self) -> LmsNetNode:
        """Returns NetNode record."""
        return self._get_data(key=RNode.Keys.NODE)  # type: ignore


class RDivision(BReportObject):
    """Report object class."""

    class Keys(object, metaclass=ReadOnlyClass):
        """Internal keys class."""

        DIVISION: str = "__div__"
        IDENT: str = "__ident__"
        NODES: str = "__nodes__"
        FOREIGN: str = "__foreign__"
        TEN: str = "__ten__"

    def __init__(
        self,
        session: Session,
        logger_queue: LoggerQueue,
        division: LmsDivision,
        verbose: bool,
        debug: bool,
    ) -> None:
        """Constructor."""

        self.logs = LoggerClient(logger_queue, self._c_name)
        self.debug = debug
        self.verbose = verbose
        self.session = session
        self._set_data(
            key=RDivision.Keys.DIVISION, value=division, set_default_type=LmsDivision
        )

        # update ident
        self.__update_ident()

        # update nodes list
        self.__get_nodes()

        # update foreign
        self.__update_foreign()

        self.logs.message_notice = (
            f"Created Division: {self.shortname}, FOREIGN: {self.foreign}"
        )

    def __repr__(self) -> str:
        """Returns string representation."""
        return f"{self._c_name}({self.division})"

    def generate_foreign(self) -> List[str]:
        """Foreign report generator."""
        head: str = "po01_id_podmiotu_obcego," "po02_nip_pl," "po03_nip_nie_pl"
        out: List[str] = []
        out.append(head)
        for item in self.foreign:  # type: ignore
            out.append(f"{item[0]},{item[1]},{item[2]}")
        return out

    def generate_nodes(self) -> List[str]:
        """Nodes report generator."""
        head: str = (
            "we01_id_wezla,"
            "we02_tytul_do_wezla,"
            "we03_id_podmiotu_obcego,"
            "we04_terc,"
            "we05_simc,"
            "we06_ulic,"
            "we07_nr_porzadkowy,"
            "we08_szerokosc,"
            "we09_dlugosc,"
            "we10_medium_transmisyjne,"
            "we11_bsa,"
            "we12_technologia_dostepowa,"
            "we13_uslugi_transmisji_danych,"
            "we14_mozliwosc_zwiekszenia_liczby_interfejsow,"
            "we15_finansowanie_publ,"
            "we16_numery_projektow_publ,"
            "we17_infrastruktura_o_duzym_znaczeniu,"
            "we18_typ_interfejsu,"
            "we19_udostepnianie_ethernet"
        )
        prefix: str = "WW_"
        out: List[str] = []
        out.append(head)
        for item in self.nodes:
            out.append(item.rep_node)
        return out

    def generate_wireless(self) -> List[str]:
        """Wireless lines generator."""
        head: str = (
            '"lb01_id_lb",'
            '"lb02_id_punktu_poczatkowego",'
            '"lb03_id_punktu_koncowego",'
            '"lb04_medium_transmisyjne",'
            '"lb05_nr_pozwolenia_radiowego",'
            '"lb06_pasmo_radiowe",'
            '"lb07_system_transmisyjny",'
            '"lb08_przepustowosc",'
            '"lb09_mozliwosc_udostepniania"'
        )
        out: List[str] = []
        out.append(head)
        return out

    def generate_cables(self) -> List[str]:
        """Cable lines generator."""
        head: str = (
            "lk01_id_lk,"
            "lk02_id_punktu_poczatkowego,"
            "lk03_punkty_zalamania,"
            "lk04_id_punktu_koncowego,"
            "lk05_medium_transmisyjne,"
            "lk06_rodzaj_linii_kablowej,"
            "lk07_liczba_wlokien,"
            "lk08_liczba_wlokien_wykorzystywanych,"
            "lk09_liczba_wlokien_udostepnienia,"
            "lk10_finansowanie_publ,"
            "lk11_numery_projektow_publ,"
            "lk12_infrastruktura_o_duzym_znaczeniu"
        )
        out: List[str] = []
        out.append(head)
        return out

    def generate_flexible_points(self) -> List[str]:
        """Flexible points generator."""
        head: str = (
            "pe01_id_pe,"
            "pe02_typ_pe,"
            "pe03_id_wezla,"
            "pe04_pdu,"
            "pe05_terc,"
            "pe06_simc,"
            "pe07_ulic,"
            "pe08_nr_porzadkowy,"
            "pe09_szerokosc,"
            "pe10_dlugosc,"
            "pe11_medium_transmisyjne,"
            "pe12_technologia_dostepowa,"
            "pe13_mozliwosc_swiadczenia_uslug,"
            "pe14_finansowanie_publ,"
            "pe15_numery_projektow_publ"
        )
        out: List[str] = []
        out.append(head)
        return out

    def generate_services(self) -> List[str]:
        """Services generator."""
        head: str = (
            '"ua01_id_punktu_adresowego",'
            '"ua02_id_pe",'
            '"ua03_id_po",'
            '"ua04_terc",'
            '"ua05_simc",'
            '"ua06_ulic",'
            '"ua07_nr_porzadkowy",'
            '"ua08_szerokosc",'
            "ua09_dlugosc,"
            "ua10_medium_dochodzace_do_pa,"
            "ua11_technologia_dostepowa,"
            "ua12_instalacja_telekom,"
            "ua13_medium_instalacji_budynku,"
            "ua14_technologia_dostepowa,"
            '"ua15_identyfikacja_uslugi",'
            '"ua16_dostep_stacjonarny",'
            '"ua17_dostep_stacjonarny_bezprzewodowy",'
            '"ua18_telewizja_cyfrowa",'
            '"ua19_radio",'
            '"ua20_usluga_telefoniczna",'
            '"ua21_predkosc_uslugi_td",'
            '"ua22_liczba_uzytkownikow_uslugi_td"'
        )
        out: List[str] = []
        out.append(head)
        return out

    def __update_foreign(self) -> None:
        """Update foreign list."""
        out: List[List[str]] = []
        if self.main:
            rows = self.session.query(Foreign).all()
            for item in rows:
                out.append([item.ident, item.tin.replace("-", ""), ""])
        else:
            out.append([self.foreign_ident, self.ten, ""])

        self._set_data(key=RDivision.Keys.FOREIGN, value=out, set_default_type=List)

    def __update_ident(self) -> None:
        """Update IDENT if self.main is False."""
        if not self.main:
            out = (
                self.session.query(Division, LmsDivision)
                .join(LmsDivision, Division.did == LmsDivision.id)
                .filter(Division.main == True)
                .first()
            )
            if out:
                self._set_data(
                    key=RDivision.Keys.IDENT, value=out[0].ident, set_default_type=str
                )
                self._set_data(
                    key=RDivision.Keys.TEN,
                    value=out[1].ten.replace("-", ""),
                    set_default_type=str,
                )
            else:
                raise Raise.error(
                    "Could not find IDENT for main division, please check if database dataset configuration is correct.",
                    ValueError,
                    self._c_name,
                    currentframe(),
                )

    def __get_nodes(self) -> None:
        """Get nodes records from lms."""
        out: List[RNode] = []

        if self.logs and self.logs.logs_queue:

            rows = self.session.query(LmsNetNode).all()
            for item in rows:
                out.append(
                    RNode(
                        self.session,
                        self.logs.logs_queue,
                        item,
                        self.main,
                        self.foreign_ident,
                        self.verbose,
                        self.debug,
                    )
                )
            self._set_data(key=RDivision.Keys.NODES, set_default_type=List, value=out)
        else:
            raise Raise.error(
                "Logs subsystem initialization error.",
                RuntimeError,
                self._c_name,
                currentframe(),
            )

    @property
    def foreign(self) -> List[List[str]]:
        """Returns foreign list."""
        return self._get_data(key=RDivision.Keys.FOREIGN)  # type: ignore

    @property
    def foreign_ident(self) -> str:
        """Returns foreign ident string."""
        return self._get_data(
            key=RDivision.Keys.IDENT, set_default_type=str, default_value=""
        )  # type: ignore

    @property
    def ten(self) -> str:
        """Returns ten number from lms."""
        return self._get_data(
            key=RDivision.Keys.TEN, set_default_type=str, default_value=""
        )  # type: ignore

    @property
    def division(self) -> LmsDivision:
        return self._get_data(
            key=RDivision.Keys.DIVISION,
        )  # type: ignore

    @property
    def main(self) -> bool:
        """Returns True if division is the main division."""
        if not self.division:
            return False
        return self.division.map.main

    @property
    def shortname(self) -> str:
        """Returns division name."""
        if not self.division:
            return "ERROR"
        return (
            self.division.shortname.upper()
            .replace(" ", "")
            .replace(".", "")
            .replace("SPZOO", "")
            .replace("AIR-NET", "AIR-NET-")
            .strip("-")
        )

    @property
    def nodes(self) -> List[RNode]:
        """Returns RNode list."""
        return self._get_data(key=RDivision.Keys.NODES, default_value=[])  # type: ignore


# #[EOF]#######################################################################
