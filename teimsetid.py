#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pdb import set_trace
import re
import sys
import argparse
import os
from lxml import etree
import pprint
import json
from teimedlib.xml_const import *
from teimedlib.ualog import Log
from teimedlib.teimtxtread import TeimTxtRead
from teimedlib.teim_paths import *

__date__ = "01-08-2021"
__version__ = "0.4.8"
__author__ = "Marta Materni"

"""
update_xml
    read_csv
        build_tgid_js
        log_tgid_js
    parse_xml
    numerate_xml_id
        node_tgid_key
            node_tag
            node_items
                clean_key
        tgid_exists
        get_tgid_id
        init_tgid_children
            get_tgid_xid
        node_children
        updatte_node_id_descendants
            node_tgid_key
                node_tag
                node_items
                    clean_key
            tgid_exists
            next_tgid_xid
            update_node_id
            node_descendants
    numerate_xml_n
    write_xml

"""
#LOG = Log("w").open("XXX.log", 1).log


def pp(data, width=40):
    try:
        s = pprint.pformat(data, indent=0, width=width)
    except Exception as e:
        print(e)
        input("error>")
        return ""
    else:
        return s


class TeimSetId(object):
    """
    Setta gli attributi xml:id nei tag xml.
    Il criterio di aseggnazione e numerazione è
    definitio in un fule csv,

    #key | tag_id|id start|children
    div_episode||-1|div_chapter:head:cb:pb:p:lg:persName:geogName:placeName:choice
    div_chapter|chp|0|head:p:lg:l
    head|he|0|w
    cb|cb|0|
    pb|pb|0|
    p|p|0|w:pc
    lg|lg|0|    
    l|l|0|w:pc
    w|w|0|
    pc|pc|0|
    persName|peNm|0|
    geogName|geNm|0|
    placeName|plNm|0|
    choice|chc|0|

    La numerazione è definita a partire dall'elemento
    con id==-1

    Viene stampato un file json che rappresenta la
    logica dell numerazione.

    Numera <l> dopo il primo <lg> se NON hanno l'atributo n=..

    """
    TAG_ID = 'tag_id'
    ID = 'id'
    XID = 'xid'
    CHLD_LST = 'chld_lst'
    XML_ID = 'xml_id'
    XMLID = 'xml:id'
    DIV = 'div'
    TYPE = 'type'
    SPS = '                               '
    SEP = '|'

    def __init__(self, path_text, path_csv):
        self.path_text = path_text
        # testo.txt => testo_txt.txt
        self.path_in = set_path_id_in(path_text)

        # testo.txt => testo_id.xml
        self.path_out = set_path_id_out(path_text)
        self.path_csv = path_csv

        # testo.txt => testo_id.ERR.log
        path_err = set_path_id_log(path_text)
        self.log_err = Log("w").open(path_err, 1).log

        # testo.txt => testo_id.log
        path_info = set_path_id_log(path_text)
        self.log_info = Log("w").open(path_info, 0).log

        self.xml_root = etree
        self.tgid_js = {}
        self.id_cfg = {}
        # UA self.input_err_active = True
        self.input_err_active = False

    def input_err(self, msg='?'):
        if self.input_err_active:
            x = input(msg)
            if x == '.':
                self.input_err_active = False

    def build_tgid_js(self, rows):
        row = ''
        try:
            for row in rows:
                key = row[0].strip()
                tag_id = row[1].strip()
                s = row[2].strip()
                id = int(s)
                r3 = row[3].strip()
                if r3 == '':
                    chld_lst = []
                else:
                    chld_lst = r3.split(':')
                tgid = {
                    self.TAG_ID: tag_id,
                    self.ID: id,
                    self.XID: '',
                    self.CHLD_LST: chld_lst
                }
                self.tgid_js[key] = tgid
        except Exception as e:
            msg = f'ERROR. teimsetid.py build_tgid_js() \n{e}\n{row}'
            self.log_err(msg)
            sys.exit(msg)

    def log_tgid_js(self):
        try:
            path_json = self.path_out.replace(".xml", ".json")
            log_json = Log("w").open(path_json, 0).log
            s = json.dumps(self.tgid_js, indent=2)
            log_json(s)
        except Exception as e:
            msg = f'ERROR. teimsetid.py log_tgid_js() \n{e}'
            self.log_err(msg)
            sys.exit(msg)

    def read_csv(self):
        tgid_rows = []
        with open(self.path_csv, "r") as f:
            for row in f:
                try:
                    row = row.strip()
                    if row == "":
                        continue
                    if row[0] == '#':
                        continue
                    row = re.sub(r"\s{1,}", '', row)
                    flds = row.split(self.SEP)
                    tgid_rows.append(flds)
                except Exception as e:
                    msg = f'ERROR. teimsetid.py read_csv() \n{e}\n row:{row}'
                    self.log_err(msg)
                    sys.exit(msg)
        self.build_tgid_js(tgid_rows)
        self.log_tgid_js()

    ####################################

    def init_tgid_children(self, key):
        """
        resetta numeratore id di tutti i children
        lasciando la parte del genitore 
        Kchp10p3w11 => Kchp10p3w
        """
        try:
            tgn = self.tgid_js[key]
            chld_lst = tgn[self.CHLD_LST]
            xid_parent = self.get_tgid_xid(key)
            for k in chld_lst:
                tgid = self.tgid_js[k]
                tgid[self.ID] = 0
                tag_id = tgid[self.TAG_ID]
                tgid[self.XID] = f'{xid_parent}{tag_id}'
        except KeyError as e:
            msg = f'ERROR. teimsetid.py init_tgid_children() \n{e}'
            self.log_err(msg)
            sys.exit(msg)

    def set_tgid(self, key, k, v):
        try:
            self.tgid_js[key][k] = v
        except Exception as e:
            msg = f'ERROR.teimsetid.py set_tgid()\n{e}\ntag_name:{key} k:{k} v:{v}'
            self.log_err(msg)
            sys.exit(msg)

    def get_tgid(self, key):
        try:
            tgid = self.tgid_js[key]
        except Exception as e:
            msg = f'ERROR. teimsetid.py get_tgid()\n{e}\ntag_name:{key}'
            self.log_err(msg)
            sys.exit(msg)
        else:
            return tgid

    # def set_tgid_id(self, key, id):
    #     try:
    #         tgid = self.tgid_js[key]
    #         tgid[self.ID] = id
    #     except Exception as e:
    #         msg = f'ERROR. teimsetid.py set_tgid_id() \n{e}\ntag_name:{key}'
    #         self.log_err(msg)
    #         sys.exit(msg)

    def set_tgid_tag_id(self, key, tag_id):
        self.set_tgid(key, self.TAG_ID, tag_id)

    def set_tgid_xid(self, key, xid):
        self.set_tgid(key, self.XID, xid)

    def get_tgid_id(self, key):
        tgid = self.get_tgid(key)
        id = tgid[self.ID]
        return id

    def get_tgid_tag_id(self, key):
        tgid = self.get_tgid(key)
        tag_id = tgid[self.TAG_ID]
        return tag_id

    def get_tgid_xid(self, key):
        """
        rettitisce id preceduto dal suo tag
        """
        tgid = self.get_tgid(key)
        id = tgid[self.ID]
        xid = tgid[self.XID]
        if id < 0:
            sid = f'{xid}'
        else:
            sid = f'{xid}{id}'
        return sid

    def next_tgid_xid(self, key):
        """
        restituisce il successivoid preceduto dal suo tag
        """
        tgid = self.get_tgid(key)
        id = tgid[self.ID]
        xid = tgid[self.XID]
        id += 1
        tgid[self.ID] = id
        xid = f'{xid}{id}'
        return xid

    def tgid_exists(self, key):
        return key in self.tgid_js

    #####################################

    def get_id_cfg(self, key0='', key1=''):
        """
        ese.
        sign=self.id_cfg['episode']['sign']
        sign=self.id_cfg_get('episode','sign')

        """
        # sign=self.id_cfg['episode']['sign']
        try:
            js = self.id_cfg[key0]
            val = js[key1]
        except KeyError as e:
            msg = f'ERROR. id_cfg\n{e}\n '
            self.log_err(msg)
            js = pp(self.id_cfg, 30)
            self.log_err(js)
            self.input_err('?>')
            return ''
        else:
            return val

    def get_id_cfg_int(self, key0='', key1=''):
        s = self.get_id_cfg(key0, key1)
        try:
            id = int(s)
        except Exception:
            return 0
        else:
            return id

    def set_id_cfg(self, rows):
        """
        XXX testo_id.cfg default
        se testo_id.cfg non esiste utilizza i valori di default

        episode:sign=K
        episode:id=0
        chapter:n=1
        p:n=1
        l:n=1
        """
        self.id_cfg = {
            "episode": {
                "sign": "K",
                "id": '0'
            },
            "chapter": {
                "n": '1'
            },
            "p": {
                "n": '1'
            },
            "l": {
                "n": '1'
            }
        }
        for row in rows:
            try:
                sp = row.split(':')
                if len(sp) < 2:
                    continue
                key = sp[0]
                k, v = sp[1].split('=')
                k = k.strip()
                v = v.strip()
                old = self.get_id_cfg(key, k)
                if old == '':
                    v = old
                    continue
                self.id_cfg[key][k] = v.strip()
            except Exception as e:
                msg = f'ERROR temsetid.py set_id_cfg()\n{e}\n{row}'
                self.log_err(msg)

    def read_id_cfg(self):
        try:
            ttread = TeimTxtRead(self.path_text, self.log_err)
            rows = ttread.read_id_cfg()
        except Exception as e:
            msg = f'ERROR. teimsetid.py read_id_cfg() \n{e}'
            self.log_err(msg)
            sys.exit(msg)
        else:
            self.set_id_cfg(rows)

    ######################################

    def clean_key(self, k):
        s = k
        p0 = k.find("{http")
        if (p0 > -1):
            p1 = k.rfind('}')
            if p1 > -1:
                s = k[p1+1:]
        return s

    def node_liv(self, node):
        d = 0
        while node is not None:
            d += 1
            node = node.getparent()
        return d - 1

    def node_items(self, nd):
        kvs = nd.items()
        js = {}
        for kv in kvs:
            k = self.clean_key(kv[0])
            v = kv[1]
            js[k] = v
        return js

    def node_tag(self, nd):
        try:
            tag = nd.tag
            tag = tag if type(nd.tag) is str else "XXX"
            pid = tag.find('}')
            if pid > 0:
                tag = tag[pid + 1:]
        except Exception as e:
            msg = f'ERROR teimsetid.py node_tag()\n{e}'
            self.log_err(msg)
            sys, exit(msg)
        else:
            return tag.strip()

    def node_tgid_key(self, nd):
        """
        restituisce key per la lettura dal file json
        """
        tag = self.node_tag(nd)
        if tag != self.DIV:
            return tag
        attrs = self.node_items(nd)
        typx = attrs.get(self.TYPE, '')
        return f'{tag}_{typx}'

    def node_descendants(self, nd, tag=None, *tags):
        lst = []
        for nd in nd.iterdescendants(tag, *tags):
            lst.append(nd)
        return lst

    def node_children(self, nd, tag=None, *tags):
        lst = []
        for nd in nd.iterchildren(tag, *tags):
            lst.append(nd)
        return lst

    def update_node_id(self, nd, xid):
        attrs = self.node_items(nd)
        nd.attrib.clear()
        nd.set(self.XML_ID, xid)
        for k, v in attrs.items():
            nd.set(k, v)

    def updatte_node_id_descendants(self, chld_lst):
        """
        aggiorna tutti i children
        metodo chiamato ricorsivamente dalla lista 
        dei children.
        Aggiorna quindi tutti i discendenti
        """
        for nd in chld_lst:
            tgid_key = self.node_tgid_key(nd)
            if not self.tgid_exists(tgid_key):
                continue
            xid = self.next_tgid_xid(tgid_key)
            # log
            liv = self.node_liv(nd)
            self.log_info(f'{self.SPS[:liv*2]}{tgid_key} {xid}')

            self.update_node_id(nd, xid)
            self.init_tgid_children(tgid_key)
            lst = self.node_descendants(nd)
            self.updatte_node_id_descendants(lst)

    def numerate_xml_id(self):
        """
        set xml:id nei nodi secondo il criterio definito 
        nel file teimxmlid.csv e test_id.cfg
        """
        sign = self.get_id_cfg('episode', 'sign')
        eps_id = self.get_id_cfg_int('episode', 'id')
        eps_xid = f'{sign}{eps_id}' if eps_id > 0 else sign
        has_episode = False
        for nd in self.xml_root.iter(self.DIV):
            attrs = self.node_items(nd)
            # TODO if (tp := attrs.get('type', '')) == 'episode':
            tp = attrs.get('type', '')
            if tp =='episode':
                has_episode = True
            tgid_key = self.node_tgid_key(nd)
            if self.tgid_exists(tgid_key):
                id = self.get_tgid_id(tgid_key)
                if id < 0:
                    # div root identificato da id < 0
                    # setta xid di episode
                    # quindi -1 è sosituito xida
                    self.set_tgid_xid(tgid_key, eps_xid)
                    #self.set_tgid_xid(tgid_key, tag_id)
                    self.log_info(f'{tgid_key} {eps_xid}')
                    self.init_tgid_children(tgid_key)
                    chld_lst = self.node_children(nd)
                    self.updatte_node_id_descendants(chld_lst)
        if not has_episode:
            msg = f"WARNING.  {self.path_text}\nepisode Not Found "
            self.log_err(msg)
            self.input_err('>')
            # sys.exit(msg)

    def numerate_xml_l(self):
        """
        set nel tag <l> n=".."
        NON viene numerato se è prsente l'attributo n=".."
        """
        TAG = 'l'
        ATTR_N = 'n'
        n = self.get_id_cfg_int('l', 'n')
        no = n
        for nd in self.xml_root.iter(TAG):
            attrs = self.node_items(nd)
            if ATTR_N in attrs:
                continue
            nd.set(ATTR_N, str(n))
            n += 1
        return -1 if n == no else n-1

    def numerate_xml_p(self):
        """
        set nel tag <p> n=".."
        """
        TAG = 'p'
        ATTR_N = 'n'
        n = self.get_id_cfg_int('p', 'n')
        no = n
        for nd in self.xml_root.iter(TAG):
            nd.set(ATTR_N, str(n))
            n += 1
        return -1 if n == no else n-1

    def numerate_xml_chapter(self):
        """
            numera i capitoli iniziando dal valore
            settato in tetso_id.cfg
        """
        TAG = 'div'
        TYPE = 'type'
        TYPE_VAL = 'chapter'
        ATTR_n = 'n'
        n = self.get_id_cfg_int('chapter', 'n')
        no = n
        for nd in self.xml_root.iter(TAG):
            attrs = self.node_items(nd)
            # HEACK if(val := attrs.get(TYPE, '')) == TYPE_VAL:
            val = attrs.get(TYPE, '')
            if val == TYPE_VAL:
                nd.set(ATTR_n, str(n))
                n += 1
        return -1 if n == no else n-1

    def parse_xml(self):
        try:
            parser = etree.XMLParser(ns_clean=True)
            self.xml_root = etree.parse(self.path_in, parser)
        except Exception as e:
            msg = f'ERROR teimsetid.py parse_xml()\n {e}'
            self.log_err(msg)
            sys.exit(msg)

    def write_xml(self):
        try:
            xml = etree.tostring(self.xml_root,
                                 method='xml',
                                 xml_declaration=None,
                                 encoding='unicode',
                                 with_tail=True,
                                 pretty_print=True,
                                 standalone=None,
                                 doctype=None,
                                 exclusive=False,
                                 inclusive_ns_prefixes=None,
                                 strip_text=False)
            # xml_id=.. => xml:id=..
            xml = xml.replace(self.XML_ID, self.XMLID)
            with open(self.path_out, "w") as f:
                f.write(xml)
            os.chmod(self.path_out, 0o777)
        except Exception as e:
            msg = f'ERROR teimsetid.py write_xml()\n {e}'
            self.log_err(msg)
            sys.exit(msg)

    def update_xml(self):
        self.read_csv()
        self.read_id_cfg()
        self.parse_xml()
        self.numerate_xml_id()
        last_chp = self.numerate_xml_chapter()
        last_p = self.numerate_xml_p()
        last_l = self.numerate_xml_l()
        self.write_xml()

        last_chp=0 if last_chp < 0 else last_chp-1
        last_p=0 if last_p < 0 else last_p-1
        last_l=0 if last_l < 0 else last_l-1
        last=f"\nLAST:\nchapter:{last_chp}\nparagraph:{last_p}\nl:{last_l}\n"
        self.log_info(last)
        return last


def do_main(path_text,  path_csv):
    alwp = TeimSetId(path_text, path_csv)
    last=alwp.update_xml()
    return last




if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    if len(sys.argv) == 1:
        print("release: %s  %s" % (__version__, __date__))
        parser.print_help()
        sys.exit()
    parser.add_argument("-i",
                        dest="src",
                        required=True,
                        metavar="",
                        help="-i <file text>"
                        )
    parser.add_argument('-t',
                        dest="tag",
                        required=True,
                        default=" ",
                        metavar="",
                        help="-t <file.csv> (tags per gestione id)")
    args = parser.parse_args()
    do_main(args.src, args.tag)
