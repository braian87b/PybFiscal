#!/usr/bin/env python
# -*- coding: utf-8 -*-
from pyfiscalprinter.hasarPrinter import HasarPrinter #from hasarPrinter import HasarPrinter

import argparse
import platform
import sys
import re

def main(argv=None):

    #Constants
    TICKET = "TICKET"
    FORMULARIO_CONTINUO = "FORMULARIO_CONTINUO"

    #Valores por defecto:
    COM_port_prefix = ''
    COM_port = 'COM1'
    input_file = 'entrada.txt'
    output_file = 'salida.txt'
    COM_speed = 9600
    debug_on = False
    no_sincro = False

    #Plataforma (Puerto COM/Serie por defecto)
    if platform.system() == "Windows":
        #COM_port_prefix = chr(92)+chr(92)+'.'+chr(92) # '\\.\', ya que vi en unas webs que decían: 'COM1' y en otras decía '\\.\COM1'
        COM_port = 'COM1'
    elif platform.system() == "Linux":
        COM_port = '/dev/ttyS0'

    #Impresoras Compatibles (Ojo, estos listados no son los de la librería PyFiscalPrinter)
    impresora = TICKET
    modelo_impresora = '615' #es el predeterminado del driver

    if impresora == TICKET:
        modelos = 'Hasar HPR4,HPR5,H930,H951,H615,H715,H441 y Compatibles'
        modelo_impresora = '715v2'
    elif impresora == FORMULARIO_CONTINUO:
        modelos = 'Hasar HJ20,H320,H321,H322,H330,H1120,HPL8,HPL1200,NCR2008 y Compatibles'
        modelo_impresora = '320'

    modelos = '[ver modelos en la tercer URL listada abajo]'

    #Descripción y epilogo de la ayuda de comandos
    description = \
    '''
Driver para Impresoras Fiscales ''' + modelos + ''', (cc) 2014-2014 OpenSource
www: https://github.com/reingart/pyfiscalprinter
www: https://code.google.com/p/pyfiscalprinter/
www: https://code.google.com/p/pyfiscalprinter/wiki/RelevamientoCompatibilidad
Build: Ene 30 2015

Cualquier tipo de reproduccion o distribucion no autorizada de este programa
NO puede constituir ninguna severa falta civil y penal NI tampoco puede ser objeto
de acciones judiciales algunas correspondan en derecho, ya que esto es OpenSource!

Uso (Recomendado):  PybFiscal.py -p puerto -i entrada -o salida -s speed [-t][-k][-h]
Uso (Compatibilidad): ixbatch.py -p puerto -i entrada -o salida -s speed [-t][-k][-h]
    '''
    epilog = \
    '''
Ejemplos:

DOS:    ixbatch.py -p COM1 -i entrada.txt -o salida.txt -s 9600
LINUX:  ixbatch.py -p /dev/ttyS1 -i entrada.txt -o salida.txt -s 9600
UNIX:   ixbatch.py -p /dev/tty2a -i entrada.txt -o salida.txt -s 9600
    '''
    parser = argparse.ArgumentParser(description=description, epilog=epilog, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('-p', dest='COM_port', metavar='puerto', type=str, nargs='?', default=COM_port,
                        help='puerto serial donde esta conectada la impresora fiscal')
    parser.add_argument('-i', dest='input_file', metavar='entrada', type=str, nargs='?', default=input_file,
                        help='archivo de scripts con los comandos a enviar')
    parser.add_argument('-o', dest='output_file', metavar='salida', type=str, nargs='?', default=output_file,
                        help='archivo de salida con la respuestas a los comandos' + ' (AUN NO IMPLEMENTADO)')
    parser.add_argument('-s', dest='COM_speed', metavar='speed', type=int, nargs='?', default=str(COM_speed),
                        help='velocidad del puerto de comunicaciones')
    parser.add_argument('-t', dest='debug_on', action='store_const', const=True, default=debug_on,
                        help='grabar los mensajes de diagnostico en el debug.log' + ' (AUN NO IMPLEMENTADO, MODO DE TESTEO, OFFLINE)')
    parser.add_argument('-k', dest='no_sincro', action='store_const', const=True, default=no_sincro,
                        help='deshabilitar envio de @SINCRO cuando hay un error' + ' (AUN NO IMPLEMENTADO)')

    args = parser.parse_args()


    with open(args.input_file, mode='rU', buffering=1) as file: #leemos con rU (universal new-line), y con buffering=1 (1 línea)
        device = '%s%s' % (COM_port_prefix, args.COM_port)
        printer = HasarPrinter(deviceFile=device, speed=int(args.COM_speed), model=modelo_impresora, dummy=args.debug_on)

        for line in file:
            cmd = str(line.rstrip()) # cada linea es un comando, de acá para abajo laburamos con 'cmd'
            #print 'LINEA: ', cmd
            
            if cmd.endswith('|'): #quitamos último '|' al final que está al pedo
                cmd = cmd[:-1]

            if cmd.startswith('@'): #línea contiene comando
                #Respecto de 'valor_fijo' con 'T' ó 'S', T: Formulario Continuo, S: Hoja Suelta
                #(a, b, c, d) = [t(s) for t,s in zip((int,float,bool,str), re.search(regex,input).groups())]
                if cmd.startswith('@SetCustomerData'):
                    splitted = cmd.split('|')
                    if len(splitted) == 6: # tiene domicilio
                        # @SetCustomerData|SUDAMERICANA LIBROS SRL|30692137449|I|C|Mexico 564| #si es 715
                        [c, razon_social_cliente, documento_cliente, condicion_iva_cliente, 
                         tipo_documento_cliente, domicilio_comercial_cliente] = splitted
                    elif len(splitted) == 5: # NO tiene domicilio
                        # @SetCustomerData|SUDAMERICANA LIBROS SRL|30692137449|I|C| #si NO es 715
                        [c, razon_social_cliente, documento_cliente, condicion_iva_cliente,
                                tipo_documento_cliente] = splitted
                        domicilio_comercial_cliente=''

                elif cmd.startswith('@OpenFiscalReceipt'): #@OpenFiscalReceipt|A|T
                    [c, tipo_comprobante, valor_fijo] = cmd.split('|')
                    tipo_comprobante = str(tipo_comprobante).upper() #En los ejemplos de RECIBOA.TXT y RECIBOB.TXT lo tenía en minúscula.
                    numero_comprobante = printer.getLastNumber(tipo_comprobante) + 1
                    #print "imprimiendo comprobante '%s' con numero: '%s'" % (tipo_comprobante, numero_comprobante)

                    if tipo_comprobante == 'T' or tipo_comprobante == 'A' or tipo_comprobante == 'B':
                        #if tipo_comprobante == 'T':   # Ticket (Valor predeterminado)
                        #elif tipo_comprobante == 'A': # Ticket-Factura A
                        #elif tipo_comprobante == 'B': # Ticket-Factura B/C
                        printer.openBillTicket(type=tipo_comprobante, 
                                               name=razon_social_cliente, 
                                               address=domicilio_comercial_cliente, 
                                               doc=documento_cliente,
                                               docType=tipo_documento_cliente,
                                               ivaType=condicion_iva_cliente)

                    elif tipo_comprobante == 'D' or tipo_comprobante == 'E':
                        #elif tipo_comprobante == 'D': # Ticket-Nota de Débito A 'Sólo modelos SMH/P-715F, SMH/P-PR5F, y SMH/P-441F
                        #elif tipo_comprobante == 'E': # Ticket-Nota de Débito B/C 'Sólo modelos SMH/P-715F, SMH/P-PR5F, y SMH/P-441F
                        printer.openDebitNoteTicket(type=tipo_comprobante, 
                                               name=razon_social_cliente, 
                                               address=domicilio_comercial_cliente, 
                                               doc=documento_cliente,
                                               docType=tipo_documento_cliente,
                                               ivaType=condicion_iva_cliente)

                elif cmd.startswith('@PrintLineItem'):
                    #@PrintLineItem|Mouse Genius XScrol|1.0|4.08|10.50|M|0.0|0|B
                    #@PrintLineItem|Patchcord Cat.5E Gr|5.0|4.10|21.00|M|0.0|0|B
                    [c, texto_descriptivo, cantidad, precio_unitario, porcentaje_iva,
                            calificador_operacion, impuestos_internos, parametro_display, calificador_monto] = cmd.split('|')
                    printer.addItem(texto_descriptivo, float(cantidad), float(precio_unitario), float(porcentaje_iva), discount=0, discountDescription="")

                elif cmd.startswith('@Subtotal'): #@Subtotal|P|Subtotal|0|
                    [c, parametro_impresion, reservado_llenar_con_cualquier_cosa, parametro_display] = cmd.split('|')
                    
                    printer._sendCommand(printer.CMD_PRINT_SUBTOTAL, [], False)

                elif cmd.startswith('@TotalTender'): #@TotalTender|Efectivo|100.00|T|0
                    [c, texto_descripcion, monto_pagado, calificador_operacion, parametro_display] = cmd.split('|')
                    printer.addPayment(texto_descripcion, float(monto_pagado))

                elif cmd.startswith('@CloseFiscalReceipt'): #@CloseFiscalReceipt
                    printer.closeDocument()

                #**************** NO FISCAL

                elif cmd.startswith('@OpenNonFiscalReceipt'): #@OpenNonFiscalReceipt
                    printer.openNonFiscalReceipt()

                elif cmd.startswith('@PrintNonFiscalText'): #@PrintNonFiscalText|Texto NoFiscal 1|1
                    [c, texto_no_fiscal, parametro_display] = cmd.split('|')
                    printer.printNonFiscalText(texto_no_fiscal)

                elif cmd.startswith('@CloseNonFiscalReceipt'): #@CloseNonFiscalReceipt
                    printer.closeDocument() 

                elif cmd.startswith('@CloseNonFiscalReceipt'): #@CloseNonFiscalReceipt
                    printer.closeDocument() 

                #**************** Cierre Diario

                elif cmd.startswith('@DailyClose'): #@DailyClose|X
                    [c, tipo_de_reporte] = cmd.split('|')
                    printer.dailyClose(tipo_de_reporte)

                #**************** Descuento General

                elif cmd.startswith('@GeneralDiscount'): #@GeneralDiscount|Descuento 10%|9.46|m|0|T
                    [c, texto_descriptivo, monto, imputacion, parametro_display] = cmd.split('|')
                    printer.addAdditional(texto_descriptivo, monto, 0.0, negative=True) #Acá al pedo piden el iva
                    
                #**************** Textos descriptivos de Recibos

                elif cmd.startswith('@ReceiptText'): #@ReceiptText|Linea 1 En concepto de ...
                    [c, texto_lineas_recibos] = cmd.split('|')
                    printer.addReceiptDetail(texto_lineas_recibos, 0.0)

                #**************** Documento No Fiscal Homologado
                
                elif cmd.startswith('@OpenDNFH'): #@OpenDNFH|r|T|01-2345
                    splitted = cmd.split('|')
                    if len(splitted) == 6: # tiene numero, #@OpenDNFH|r|T|01-2345
                        [c, tipo_de_documento, valor_fijo, identificacion_del_documento] = splitted
                    elif len(splitted) == 5: # NO tiene numero, #@OpenDNFH|r|T
                        [c, tipo_de_documento, valor_fijo] = splitted
                        identificacion_del_documento = ''
                    
                    if tipo_de_documento == 'R':   # Nota Credito A
                        printer.openBillCreditTicket(type=tipo_de_documento,
                                                     name=razon_social_cliente,
                                                     address=domicilio_comercial_cliente,
                                                     doc=documento_cliente,
                                                     docType=tipo_documento_cliente,
                                                     ivaType=condicion_iva_cliente,
                                                     reference='NC')
                    
                    elif tipo_de_documento == 'S': # Nota Credito B
                        printer.openBillCreditTicket(type=tipo_de_documento,
                                                     name=razon_social_cliente,
                                                     address=domicilio_comercial_cliente,
                                                     doc=documento_cliente,
                                                     docType=tipo_documento_cliente,
                                                     ivaType=condicion_iva_cliente,
                                                     reference='NC')
                    
                    elif tipo_de_documento == 'X' or tipo_de_documento == 'x': # Recibo
                        printer.openReceipt(name=razon_social_cliente,
                                            address=domicilio_comercial_cliente,
                                            doc=documento_cliente,
                                            docType=tipo_documento_cliente,
                                            ivaType=condicion_iva_cliente,
                                            number=identificacion_del_documento,
                                            copies=1)
                    
                    elif tipo_de_documento == 'r': # Remito
                        printer.openRemit(name=razon_social_cliente,
                                          address=domicilio_comercial_cliente,
                                          doc=documento_cliente,
                                          docType=tipo_documento_cliente,
                                          ivaType=condicion_iva_cliente,
                                          copies=1)
                    
                    else:
                        pass
                    
                elif cmd.startswith('@CloseDNFH'): #@CloseDNFH
                    printer.closeDocument()
                    

                #**************** Imprimir item en remito u orden de salida

                elif cmd.startswith('@PrintEmbarkItem'): #@PrintEmbarkItem|Mouse Genius XScroll Optico Negro Ps/2|1.0|0
                    [c, descripcion_item, cantidad, parametro_display] = cmd.split('|')
                    printer.addRemitItem(descripcion_item, cantidad)

                #**************** Cargar información remito / comprobante original

                elif cmd.startswith('@SetEmbarkNumber'): #@SetEmbarkNumber|1|01-2345
                    [c, numero_linea_remito_comprobante_original, texto_de_descripcion] = cmd.split('|')
                    print "en PyFiscalPrinter no encontré'en donde aplica '@SetEmbarkNumber'"

                elif cmd.startswith('@'):
                    print 'No se como ejecutar el comando:', cmd
            else: # not cmd.startswith('@'): #línea NO contiene comando
                if len(cmd.strip()) > 1:
                    print 'Linea no contiene comando:', cmd
        #Termino de leer el archivo
        printer.close() # Libero el puerto de la impresora fiscal

    #Archivo cerrado.
    #raw_input(' a ver')
    exit()


if __name__ == "__main__":
    sys.exit(main())