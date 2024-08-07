import json,os,datetime,requests,csv,zipfile,io
from dateutil import parser
from libfptr10 import IFptr
def readNextRecord(fptr, recordsID):
    fptr.setParam(IFptr.LIBFPTR_PARAM_RECORDS_ID, recordsID)
    return fptr.readNextRecord()

def printable(offset, tag_name, tag_number, tag_value, new_line_before_value, new_line_after_value):
    return '{}{} ({}): {}{}{}'.format(offset * '  ',
                                    tag_name,
                                    tag_number,
                                    '\n' if new_line_before_value else '',
                                    tag_value,
                                    '\n' if new_line_after_value else '')


def parse(fptr, print_offset, tag_name, tag_value, tag_number, tag_type):
    if tag_type in [IFptr.LIBFPTR_TAG_TYPE_BITS, IFptr.LIBFPTR_TAG_TYPE_BYTE, IFptr.LIBFPTR_TAG_TYPE_UINT_16,
                    IFptr.LIBFPTR_TAG_TYPE_UINT_32]:
        return printable(print_offset, tag_name, tag_number, fptr.getParamInt(IFptr.LIBFPTR_PARAM_TAG_VALUE), False, True)
    elif tag_type in [IFptr.LIBFPTR_TAG_TYPE_VLN]:
        return printable(print_offset, tag_name, tag_number, fptr.getParamDouble(IFptr.LIBFPTR_PARAM_TAG_VALUE), False, True)
    elif tag_type in [IFptr.LIBFPTR_TAG_TYPE_FVLN]:
        return printable(print_offset, tag_name, tag_number, fptr.getParamDouble(IFptr.LIBFPTR_PARAM_TAG_VALUE), False, True)
    elif tag_type in [IFptr.LIBFPTR_TAG_TYPE_BOOL]:
        return printable(print_offset, tag_name, tag_number, fptr.getParamBool(IFptr.LIBFPTR_PARAM_TAG_VALUE), False, True)
    elif tag_type in [IFptr.LIBFPTR_TAG_TYPE_ARRAY]:
        return printable(print_offset, tag_name, tag_number, fptr.getParamByteArray(IFptr.LIBFPTR_PARAM_TAG_VALUE), False, True)
    elif tag_type in [IFptr.LIBFPTR_TAG_TYPE_STRING]:
        return printable(print_offset, tag_name, tag_number, fptr.getParamString(IFptr.LIBFPTR_PARAM_TAG_VALUE), False, True)
    elif tag_type in [IFptr.LIBFPTR_TAG_TYPE_UNIX_TIME]:
        return printable(print_offset, tag_name, tag_number, fptr.getParamDateTime(IFptr.LIBFPTR_PARAM_TAG_VALUE), False, True)
    elif tag_type in [IFptr.LIBFPTR_TAG_TYPE_STLV]:
        fptr.setParam(IFptr.LIBFPTR_PARAM_RECORDS_TYPE, IFptr.LIBFPTR_RT_PARSE_COMPLEX_ATTR)
        fptr.setParam(IFptr.LIBFPTR_PARAM_TAG_VALUE, tag_value)
        fptr.beginReadRecords()
        records_id = fptr.getParamString(IFptr.LIBFPTR_PARAM_RECORDS_ID)

        result = ''
        while read_next_record(fptr, records_id) == 0:
            result += parse(fptr, print_offset + 1,
                            fptr.getParamString(IFptr.LIBFPTR_PARAM_TAG_NAME),
                            fptr.getParamByteArray(IFptr.LIBFPTR_PARAM_TAG_VALUE),
                            fptr.getParamInt(IFptr.LIBFPTR_PARAM_TAG_NUMBER),
                            fptr.getParamInt(IFptr.LIBFPTR_PARAM_TAG_TYPE))

        end_read_records(fptr, records_id)
        return printable(print_offset, tag_name, tag_number, result, True, False)
    else:
        return ''
    
def read_next_record(fptr, records_id):
    fptr.setParam(IFptr.LIBFPTR_PARAM_RECORDS_ID, records_id)
    return fptr.readNextRecord()


def end_read_records(fptr, records_id):
    fptr.setParam(IFptr.LIBFPTR_PARAM_RECORDS_ID, records_id)
    return fptr.endReadRecords()

# Открытие чека прихода
def ReceiptSellOpen(fptr):
    fptr.setParam(1021, "Системный администратор")
    #fptr.setParam(1203, "123456789047")
    fptr.operatorLogin()

    fptr.setParam(IFptr.LIBFPTR_PARAM_RECEIPT_TYPE, IFptr.LIBFPTR_RT_SELL)
    fptr.openReceipt()

# Открытие чека коррекции прихода
def ReceiptSellCorrectionOpen(fptr,correctionDate,additionalTags=[]):
    fptr.setParam(1178, correctionDate)
    #fptr.setParam(1179, "№1234")
    fptr.utilFormTlv()
    correctionInfo = fptr.getParamByteArray(IFptr.LIBFPTR_PARAM_TAG_VALUE)
    fptr.setParam(IFptr.LIBFPTR_PARAM_RECEIPT_TYPE, IFptr.LIBFPTR_RT_SELL_CORRECTION)
    fptr.setParam(1173, 0)
    fptr.setParam(1174, correctionInfo)
    for tag in additionalTags:
        fptr.setParam(tag['tagNumber'],tag['tagValue'])
    fptr.openReceipt()

# Открытие чека коррекции возврата прихода
def ReceiptSellReturnCorrectionOpen(fptr,correctionDate,additionalTags=[]):
    fptr.setParam(1178, correctionDate)
    #fptr.setParam(1179, "№1234")
    fptr.utilFormTlv()
    correctionInfo = fptr.getParamByteArray(IFptr.LIBFPTR_PARAM_TAG_VALUE)
    fptr.setParam(IFptr.LIBFPTR_PARAM_RECEIPT_TYPE, IFptr.LIBFPTR_RT_SELL_RETURN_CORRECTION)
    fptr.setParam(1173, 0)
    fptr.setParam(1174, correctionInfo)
    for tag in additionalTags:
        fptr.setParam(tag['tagNumber'],tag['tagValue'])    
    fptr.openReceipt()

# Позиция в чеке
def registration(fptr,wareName,price,quantity,sum,tax,measureUnit=0):
    fptr.setParam(IFptr.LIBFPTR_PARAM_COMMODITY_NAME,wareName)
    fptr.setParam(IFptr.LIBFPTR_PARAM_PRICE,price)
    fptr.setParam(IFptr.LIBFPTR_PARAM_QUANTITY,quantity)
    fptr.setParam(IFptr.LIBFPTR_PARAM_POSITION_SUM,sum)
    fptr.setParam(IFptr.LIBFPTR_PARAM_TAX_TYPE,tax)
    fptr.setParam(2108,measureUnit)
    fptr.registration()

# Оплата в чеке
def payment(fptr,type,sum):
    # if type == 0:
    #     fptr.setParam(IFptr.LIBFPTR_PARAM_PAYMENT_TYPE,IFptr.LIBFPTR_PT_CASH)
    # elif type == 1:
    #     fptr.setParam(IFptr.LIBFPTR_PARAM_PAYMENT_TYPE,IFptr.LIBFPTR_PT_ELECTRONICALLY)
    # else:
    #     fptr.setParam(IFptr.LIBFPTR_PARAM_PAYMENT_TYPE,IFptr.LIBFPTR_PT_CASH)
    fptr.setParam(IFptr.LIBFPTR_PARAM_PAYMENT_TYPE,type)
    fptr.setParam(IFptr.LIBFPTR_PARAM_PAYMENT_SUM,sum)
    fptr.payment()

# Итог чека
def receiptTotal(fptr,sum):
    fptr.setParam(IFptr.LIBFPTR_PARAM_SUM,sum)
    fptr.receiptTotal()

# Закрытие чека
def receiptClose(fptr):
    fptr.closeReceipt()
    while fptr.checkDocumentClosed() < 0:
        # Не удалось проверить состояние документа. Вывести пользователю текст ошибки, попросить устранить неполадку и повторить запрос
        print(fptr.errorDescription())
        input("Press any key to continue")
        continue

    while not fptr.getParamBool(IFptr.LIBFPTR_PARAM_DOCUMENT_CLOSED):
        # Документ не закрылся. Требуется его отменить (если это чек) и сформировать заново
        fptr.cancelReceipt()
        input("Press any key to continue")
        return 1

    if not fptr.getParamBool(IFptr.LIBFPTR_PARAM_DOCUMENT_PRINTED):
        # Можно сразу вызвать метод допечатывания документа, он завершится с ошибкой, если это невозможно
        while fptr.continuePrint() < 0:
            # Если не удалось допечатать документ - показать пользователю ошибку и попробовать еще раз.
            print('Не удалось напечатать документ (Ошибка "%s"). Устраните неполадку и повторите.', fptr.errorDescription())
            input("Press any key to continue")
            continue
    return 0

# isOpened = fptr.isOpened()

# fptr.setParam(IFptr.LIBFPTR_PARAM_DATA_TYPE, IFptr.LIBFPTR_DT_STATUS)
# fptr.queryData()

# operatorID      = fptr.getParamInt(IFptr.LIBFPTR_PARAM_OPERATOR_ID)
# logicalNumber   = fptr.getParamInt(IFptr.LIBFPTR_PARAM_LOGICAL_NUMBER)
# shiftState      = fptr.getParamInt(IFptr.LIBFPTR_PARAM_SHIFT_STATE)
# model           = fptr.getParamInt(IFptr.LIBFPTR_PARAM_MODEL)
# mode            = fptr.getParamInt(IFptr.LIBFPTR_PARAM_MODE)
# submode         = fptr.getParamInt(IFptr.LIBFPTR_PARAM_SUBMODE)
# receiptNumber   = fptr.getParamInt(IFptr.LIBFPTR_PARAM_RECEIPT_NUMBER)
# documentNumber  = fptr.getParamInt(IFptr.LIBFPTR_PARAM_DOCUMENT_NUMBER)
# shiftNumber     = fptr.getParamInt(IFptr.LIBFPTR_PARAM_SHIFT_NUMBER)
# receiptType     = fptr.getParamInt(IFptr.LIBFPTR_PARAM_RECEIPT_TYPE)
# documentType    = fptr.getParamInt(IFptr.LIBFPTR_PARAM_DOCUMENT_TYPE)
# lineLength      = fptr.getParamInt(IFptr.LIBFPTR_PARAM_RECEIPT_LINE_LENGTH)
# lineLengthPix   = fptr.getParamInt(IFptr.LIBFPTR_PARAM_RECEIPT_LINE_LENGTH_PIX)

# receiptSum = fptr.getParamDouble(IFptr.LIBFPTR_PARAM_RECEIPT_SUM)

# isOperatorRegistered    = fptr.getParamBool(IFptr.LIBFPTR_PARAM_OPERATOR_REGISTERED)
# isFiscalDevice          = fptr.getParamBool(IFptr.LIBFPTR_PARAM_FISCAL)
# isFiscalFN              = fptr.getParamBool(IFptr.LIBFPTR_PARAM_FN_FISCAL)
# isFNPresent             = fptr.getParamBool(IFptr.LIBFPTR_PARAM_FN_PRESENT)
# isInvalidFN             = fptr.getParamBool(IFptr.LIBFPTR_PARAM_INVALID_FN)
# isCashDrawerOpened      = fptr.getParamBool(IFptr.LIBFPTR_PARAM_CASHDRAWER_OPENED)
# isPaperPresent          = fptr.getParamBool(IFptr.LIBFPTR_PARAM_RECEIPT_PAPER_PRESENT)
# isPaperNearEnd          = fptr.getParamBool(IFptr.LIBFPTR_PARAM_PAPER_NEAR_END)
# isCoverOpened           = fptr.getParamBool(IFptr.LIBFPTR_PARAM_COVER_OPENED)
# isPrinterConnectionLost = fptr.getParamBool(IFptr.LIBFPTR_PARAM_PRINTER_CONNECTION_LOST)
# isPrinterError          = fptr.getParamBool(IFptr.LIBFPTR_PARAM_PRINTER_ERROR)
# isCutError              = fptr.getParamBool(IFptr.LIBFPTR_PARAM_CUT_ERROR)
# isPrinterOverheat       = fptr.getParamBool(IFptr.LIBFPTR_PARAM_PRINTER_OVERHEAT)
# isDeviceBlocked         = fptr.getParamBool(IFptr.LIBFPTR_PARAM_BLOCKED)

# dateTime = fptr.getParamDateTime(IFptr.LIBFPTR_PARAM_DATE_TIME)

# serialNumber    = fptr.getParamString(IFptr.LIBFPTR_PARAM_SERIAL_NUMBER)
# modelName       = fptr.getParamString(IFptr.LIBFPTR_PARAM_MODEL_NAME)
# firmwareVersion = fptr.getParamString(IFptr.LIBFPTR_PARAM_UNIT_VERSION)

# fptr.setParam(IFptr.LIBFPTR_PARAM_RECORDS_TYPE, IFptr.LIBFPTR_RT_LAST_DOCUMENT_LINES)
# fptr.beginReadRecords()
# recordsID = fptr.getParamString(IFptr.LIBFPTR_PARAM_RECORDS_ID)

# while readNextRecord(fptr, recordsID) == IFptr.LIBFPTR_OK:
#     textLine        = fptr.getParamString(IFptr.LIBFPTR_PARAM_TEXT)
#     font            = fptr.getParamInt(IFptr.LIBFPTR_PARAM_FONT)
#     linespacing     = fptr.getParamInt(IFptr.LIBFPTR_PARAM_LINESPACING)
#     brightness      = fptr.getParamInt(IFptr.LIBFPTR_PARAM_BRIGHTNESS)
#     doubleWidth     = fptr.getParamBool(IFptr.LIBFPTR_PARAM_FONT_DOUBLE_WIDTH)
#     doubleHeight    = fptr.getParamBool(IFptr.LIBFPTR_PARAM_FONT_DOUBLE_HEIGHT)

# fptr.setParam(IFptr.LIBFPTR_PARAM_RECORDS_ID, recordsID)
# fptr.endReadRecords()

# fptr.setParam(IFptr.LIBFPTR_PARAM_RECORDS_TYPE, IFptr.LIBFPTR_RT_LAST_DOCUMENT_LINES)
# fptr.beginReadRecords()
# recordsID = fptr.getParamString(IFptr.LIBFPTR_PARAM_RECORDS_ID)

# while readNextRecord(fptr, recordsID) == IFptr.LIBFPTR_OK:
#     textLine        = fptr.getParamString(IFptr.LIBFPTR_PARAM_TEXT)
#     font            = fptr.getParamInt(IFptr.LIBFPTR_PARAM_FONT)
#     linespacing     = fptr.getParamInt(IFptr.LIBFPTR_PARAM_LINESPACING)
#     brightness      = fptr.getParamInt(IFptr.LIBFPTR_PARAM_BRIGHTNESS)
#     doubleWidth     = fptr.getParamBool(IFptr.LIBFPTR_PARAM_FONT_DOUBLE_WIDTH)
#     doubleHeight    = fptr.getParamBool(IFptr.LIBFPTR_PARAM_FONT_DOUBLE_HEIGHT)

# fptr.setParam(IFptr.LIBFPTR_PARAM_RECORDS_ID, recordsID)
# fptr.endReadRecords()

def receiptShowReadable(fptr,fdNumber):
    fptr.setParam(IFptr.LIBFPTR_PARAM_RECORDS_TYPE, IFptr.LIBFPTR_RT_FN_DOCUMENT_TLVS)
    fptr.setParam(IFptr.LIBFPTR_PARAM_DOCUMENT_NUMBER, fdNumber)
    fptr.beginReadRecords()

    #documentType = fptr.getParamInt(IFptr.LIBFPTR_PARAM_FN_DOCUMENT_TYPE)
    #documentSize = fptr.getParamInt(IFptr.LIBFPTR_PARAM_COUNT)
    recordsID = fptr.getParamString(IFptr.LIBFPTR_PARAM_RECORDS_ID)

# fdList = []
# if(documentType == fptr.LIBFPTR_FN_DOC_RECEIPT):
#     fdTags = []
#     while readNextRecord(fptr, recordsID) == IFptr.LIBFPTR_OK:
#         tagValue      = fptr.getParamByteArray(IFptr.LIBFPTR_PARAM_TAG_VALUE)
#         tagNumber     = fptr.getParamInt(IFptr.LIBFPTR_PARAM_TAG_NUMBER)
#         tagName       = fptr.getParamString(IFptr.LIBFPTR_PARAM_TAG_NAME)
#         tagType       = fptr.getParamInt(IFptr.LIBFPTR_PARAM_TAG_TYPE)
#         tagIsComplex  = fptr.getParamBool(IFptr.LIBFPTR_PARAM_TAG_IS_COMPLEX)
#         tagRepeatable = fptr.getParamBool(IFptr.LIBFPTR_PARAM_TAG_IS_REPEATABLE)
#         fdTags.append({"value": tagValue,
#                    "number": tagNumber,
#                    "name": tagName,
#                    "type": tagType,
#                    "isComplex": tagIsComplex,
#                    "repeatable": tagRepeatable})
#     fd = {"number": fdNumber,
#             "tags": fdTags}
#     fdList.append(fd)
#     fdListSerialized = json.dumps(fdList)

# fptr.setParam(IFptr.LIBFPTR_PARAM_RECORDS_ID, recordsID)
# fptr.endReadRecords()

# fptr.close()

    result = ''
    while read_next_record(fptr, recordsID) == 0:
        result += parse(fptr, 0,
                        fptr.getParamString(IFptr.LIBFPTR_PARAM_TAG_NAME),
                        fptr.getParamByteArray(IFptr.LIBFPTR_PARAM_TAG_VALUE),
                        fptr.getParamInt(IFptr.LIBFPTR_PARAM_TAG_NUMBER),
                        fptr.getParamInt(IFptr.LIBFPTR_PARAM_TAG_TYPE))

    end_read_records(fptr, recordsID)

    #fptr.close()

    print(result)

def receiptsRead(fptr,fdNumber):
    wares = []
    payments = []

    #fdTags = []
    fptr.setParam(IFptr.LIBFPTR_PARAM_RECORDS_TYPE, IFptr.LIBFPTR_RT_FN_DOCUMENT_TLVS)
    fptr.setParam(IFptr.LIBFPTR_PARAM_DOCUMENT_NUMBER, fdNumber)
    fptr.beginReadRecords()
    fdType = fptr.getParamInt(IFptr.LIBFPTR_PARAM_FN_DOCUMENT_TYPE)
    if fdType in [IFptr.LIBFPTR_FN_DOC_RECEIPT]:
        recordsID = fptr.getParamString(IFptr.LIBFPTR_PARAM_RECORDS_ID)
        while read_next_record(fptr, recordsID) == 0:
            #tagName = fptr.getParamString(IFptr.LIBFPTR_PARAM_TAG_NAME)
            tagValue = fptr.getParamByteArray(IFptr.LIBFPTR_PARAM_TAG_VALUE)
            tagNumber = fptr.getParamInt(IFptr.LIBFPTR_PARAM_TAG_NUMBER)
            #tagType = fptr.getParamInt(IFptr.LIBFPTR_PARAM_TAG_TYPE) 
            
            if tagNumber == 1012:
                fdDate = fptr.getParamDateTime(IFptr.LIBFPTR_PARAM_TAG_VALUE)
            elif tagNumber == 1020:
                receiptTotal = fptr.getParamDouble(IFptr.LIBFPTR_PARAM_TAG_VALUE)
            elif tagNumber == 1059:
                wares.append(getWareData(fptr,tagValue))
            elif tagNumber == 1031:
                payments.append({"type":IFptr.LIBFPTR_PT_CASH,"sum":fptr.getParamDouble(IFptr.LIBFPTR_PARAM_TAG_VALUE)})
            elif tagNumber == 1081:
                payments.append({"type":IFptr.LIBFPTR_PT_ELECTRONICALLY,"sum":fptr.getParamDouble(IFptr.LIBFPTR_PARAM_TAG_VALUE)})
            
            #fdTags.append(getTagStructure(fptr,tagName,tagValue,tagNumber,tagType))
        
        end_read_records(fptr, recordsID)

        receipt = {"fdType": fdType,
                "fdNumber": fdNumber,
                "fdDate": fdDate,
                "total": receiptTotal,
                "wares": wares,
                "payments": payments}
        
        return receipt

        #return fdTags

def getWareData(fptr,tagValue):
    #fdTags = []

    fptr.setParam(IFptr.LIBFPTR_PARAM_RECORDS_TYPE, IFptr.LIBFPTR_RT_PARSE_COMPLEX_ATTR)
    fptr.setParam(IFptr.LIBFPTR_PARAM_TAG_VALUE, tagValue)

    fptr.beginReadRecords()
    records_id = fptr.getParamString(IFptr.LIBFPTR_PARAM_RECORDS_ID)
    while read_next_record(fptr, records_id) == 0:
        #tagName = fptr.getParamString(IFptr.LIBFPTR_PARAM_TAG_NAME)
        #tagValue = fptr.getParamByteArray(IFptr.LIBFPTR_PARAM_TAG_VALUE)
        tagNumber = fptr.getParamInt(IFptr.LIBFPTR_PARAM_TAG_NUMBER)
        #tagType = fptr.getParamInt(IFptr.LIBFPTR_PARAM_TAG_TYPE) 
        #fdTags.append(getTagStructure(fptr,tagName,tagValue,tagNumber,tagType))
        #return fdTags
        if tagNumber == 1030:
            wareName = fptr.getParamString(IFptr.LIBFPTR_PARAM_TAG_VALUE)
        elif tagNumber == 1079:
            price = fptr.getParamDouble(IFptr.LIBFPTR_PARAM_TAG_VALUE)
        elif tagNumber == 1023:
            quantity = fptr.getParamDouble(IFptr.LIBFPTR_PARAM_TAG_VALUE)
        elif tagNumber == 1043:
            sum = fptr.getParamDouble(IFptr.LIBFPTR_PARAM_TAG_VALUE)
        elif tagNumber == 1199:
            tax = fptr.getParamInt(IFptr.LIBFPTR_PARAM_TAG_VALUE)
    wareData = {"name": wareName,
                "price": price,
                "quantity": quantity,
                "sum": sum,
                "tax": tax}
    return wareData

def getTagStructure(fptr,tagName,tagValue,tagNumber,tagType):
    if tagType in [IFptr.LIBFPTR_TAG_TYPE_STLV]:
            fdTags = []
            fptr.setParam(IFptr.LIBFPTR_PARAM_RECORDS_TYPE, IFptr.LIBFPTR_RT_PARSE_COMPLEX_ATTR)
            fptr.setParam(IFptr.LIBFPTR_PARAM_TAG_VALUE, tagValue)
            fptr.beginReadRecords()
            records_id = fptr.getParamString(IFptr.LIBFPTR_PARAM_RECORDS_ID)
            while read_next_record(fptr, records_id) == 0:
                tagName = fptr.getParamString(IFptr.LIBFPTR_PARAM_TAG_NAME)
                tagValue = fptr.getParamByteArray(IFptr.LIBFPTR_PARAM_TAG_VALUE)
                tagNumber = fptr.getParamInt(IFptr.LIBFPTR_PARAM_TAG_NUMBER)
                tagType = fptr.getParamInt(IFptr.LIBFPTR_PARAM_TAG_TYPE) 
                fdTags.append(getTagStructure(fptr,tagName,tagValue,tagNumber,tagType))
            return fdTags
    else:
        return {"tagName": tagName,
                "tagValue": tagValue,
                "tagNumber": tagNumber,
                "tagType": tagType}

# Чек прихода
def receiptSell(fptr,positions,payments):
    ReceiptSellOpen(fptr)
    sum = 0
    for position in positions:
        if 'measureUnit' in position:
            registration(fptr,position['wareName'],position['price'],position['quantity'],position['sum'],position['tax'],position['measureUnit'])
        else:
            registration(fptr,position['wareName'],position['price'],position['quantity'],position['sum'],position['tax'])
        sum += position['sum']
    for pay in payments:
        payment(fptr,pay['type'],pay['sum'])
    receiptTotal(fptr,sum)
    return receiptClose(fptr)

def receiptSellCorrection(fptr,correctionDate,positions,payments,additionalTags=[]):
    ReceiptSellCorrectionOpen(fptr,correctionDate,additionalTags)
    sum = 0
    for position in positions:
        if 'measureUnit' in position:
            registration(fptr,position['name'],position['price'],position['quantity'],position['sum'],position['tax'],position['measureUnit'])
        else:
            registration(fptr,position['name'],position['price'],position['quantity'],position['sum'],position['tax'])
        sum += position['sum']
    for pay in payments:
        payment(fptr,pay['type'],pay['sum'])
    receiptTotal(fptr,sum)
    return receiptClose(fptr)

def receiptSellReturnCorrection(fptr,correctionDate,positions,payments,additionalTags=[]):
    ReceiptSellReturnCorrectionOpen(fptr,correctionDate,additionalTags)
    sum = 0
    for position in positions:
        if 'measureUnit' in position:
            registration(fptr,position['name'],position['price'],position['quantity'],position['sum'],position['tax'],position['measureUnit'])
        else:
            registration(fptr,position['name'],position['price'],position['quantity'],position['sum'],position['tax'])
        sum += position['sum']
    for pay in payments:
        payment(fptr,pay['type'],pay['sum'])
    receiptTotal(fptr,sum)
    return receiptClose(fptr)

def getLastFd(fptr):
    fptr.setParam(IFptr.LIBFPTR_PARAM_FN_DATA_TYPE, IFptr.LIBFPTR_FNDT_LAST_DOCUMENT)
    fptr.fnQueryData()
    documentNumber = fptr.getParamInt(IFptr.LIBFPTR_PARAM_DOCUMENT_NUMBER)
    return documentNumber

def getReceiptFromTlv(tlv):  
    wares = []
    payments = []      
    buyerPhoneOrAddress = ''
    receiptType = tlv['1054']
    fdNumber = tlv['1040']
    if "1031" in tlv:
        payments.append({"type":IFptr.LIBFPTR_PT_CASH,"sum":tlv["1031"]/100})
    if "1081" in tlv:
        payments.append({"type":IFptr.LIBFPTR_PT_ELECTRONICALLY,"sum":tlv["1081"]/100})
    if "1008" in tlv:
        buyerPhoneOrAddress = tlv['1008']
    
    taxType = tlv['1055']
    fdDate = parser.parse(tlv['1012'])
    receiptTotal = tlv['1020'] / 100
    for ware in tlv["1059"]:
        measureUnit = 0
        if '2108' in ware:
            measureUnit = ware['2108']
        wares.append({
            "name": ware['1030'],
            "price": ware['1079'] / 100,
            "quantity": ware['1023'],
            "sum": ware['1043'] / 100,
            "tax": ware['1199'],
            "measureUnit": measureUnit
        })

    receipt = {
            "receiptType": receiptType,
            "fdNumber": fdNumber,
            "fdDate": fdDate,
            "total": receiptTotal,
            "buyerPhoneOrAddress": buyerPhoneOrAddress,
            "taxType": taxType,
            "wares": wares,
            "payments": payments
        }
    
    return receipt

# OFD.RU
def receiptOfd1Read(kktAgreementId,docNumber,customFnNumber,cookie):
    receipt = None
    url = 'https://lk.ofd.ru/api/Customer/GetJsonDoc'
    headers = {
        'User-Agent': 'Python',
        'Cookie': cookie
    }
    params = {
        'KktAgreementId': kktAgreementId,
        'DocNumber': docNumber,
        'CustomFnNumber': customFnNumber
    }
    try:
        response = requests.get(url=url,headers=headers,params=params)
        responseObj = json.loads(response.text)
        tlv = responseObj['Data']['TlvDictionary']
        receipt = getReceiptFromTlv(tlv)
    except ConnectionError:
        pass
    except:
        pass

    return receipt

def getTlvFromOfd2Json(responseObj):
    keys = []
    for key in responseObj:
        keys.append(key)
    for key in keys:
        if key == "fiscalDocumentFormatVer":
            responseObj['1209'] = responseObj.pop(key)
        elif key == "fiscalDriveNumber":
            responseObj['1041'] = responseObj.pop(key)
        elif key == "kktRegId":
            responseObj['1037'] = responseObj.pop(key)
        elif key == "userInn":
            responseObj['1018'] = responseObj.pop(key)
        elif key == "fiscalDocumentNumber":
            responseObj['1040'] = responseObj.pop(key)
        elif key == "dateTime":
            responseObj['1012'] = datetime.datetime.fromtimestamp(responseObj.pop(key) - 3600*11).isoformat()
        elif key == "fiscalSign":
            responseObj['1077'] = responseObj.pop(key)
        elif key == "shiftNumber":
            responseObj['1038'] = responseObj.pop(key)
        elif key == "requestNumber":
            responseObj['1042'] = responseObj.pop(key)
        elif key == "operationType":
            responseObj['1054'] = responseObj.pop(key)
        elif key == "totalSum":
            responseObj['1020'] = responseObj.pop(key)
        elif key == "buyerPhoneOrAddress":
            responseObj['1008'] = responseObj.pop(key)
        elif key == "items":
            responseObj['1059'] = responseObj.pop(key)
        elif key == "cashTotalSum":
            responseObj['1031'] = responseObj.pop(key)
        elif key == "ecashTotalSum":
            responseObj['1081'] = responseObj.pop(key)
        elif key == "prepaidSum":
            responseObj['1215'] = responseObj.pop(key)
        elif key == "creditSum":
            responseObj['1216'] = responseObj.pop(key)
        elif key == "provisionSum":
            responseObj['1217'] = responseObj.pop(key)
        elif key == "ndsNo":
            responseObj['1105'] = responseObj.pop(key)
        elif key == "taxationType":
            responseObj['1055'] = responseObj.pop(key)
        elif key == "operator":
            responseObj['1021'] = responseObj.pop(key)
        elif key == "operatorInn":
            responseObj['1203'] = responseObj.pop(key)
        elif key == "retailAddress":
            responseObj['1009'] = responseObj.pop(key)
        elif key == "retailPlace":
            responseObj['1187'] = responseObj.pop(key)
    
    for item in responseObj['1059']:
        keys = []
        for key in item:
            keys.append(key)
        for key in keys:
            if key == "measureUnit":
                item['2108'] = item.pop(key)
            elif key == "name":
                item['1030'] = item.pop(key)
            elif key == "price":
                item['1079'] = item.pop(key)
            elif key == "quantity":
                item['1023'] = item.pop(key)
            elif key == "sum":
                item['1043'] = item.pop(key)
            elif key == "nds":
                item['1199'] = item.pop(key)
            elif key == "paymentType":
                item['1214'] = item.pop(key)
            elif key == "productType":
                item['1212'] = item.pop(key)

    return responseObj
# PLATFORMAOFD.RU
def receiptOfd2Read(id,date,fp,cookie):
    receipt = None
    url = 'https://lk.platformaofd.ru/web/auth/cheques/json'
    headers = {
        'User-Agent': 'Python',
        'Cookie': cookie
    }
    params = {
        'id': id,
        'date': date,
        'fp': fp
    }
    try:
        response = requests.get(url=url,headers=headers,params=params)
        iostring = io.BytesIO(response.content)
        zipJson = zipfile.ZipFile(iostring)
        responseObj = json.loads(zipJson.read('cheque_' + id + '.txt'))
        tlv = getTlvFromOfd2Json(responseObj)
        receipt = getReceiptFromTlv(tlv)
    except ConnectionError:
        pass
    except:
        pass

    return receipt

# Загрузка чеков с ЛК ОФД
# ofdProvider:
#   1 - OFD.RU
#   2 - PLATFORMAOFD.RU    
def loadOfdDocs(fdLinksPath,ofdProvider):
    receipts = []
    cookie = input("OFD Cookie: ")
    with open(fdLinksPath, newline='') as csvfile:
        params = csv.DictReader(csvfile, delimiter=',')
        for param in params:
            receiptNotLoaded = True
            while receiptNotLoaded:
                if ofdProvider == 1:
                    receipt = receiptOfd1Read(param['KktAgreementId'],param['DocNumber'],param['CustomFnNumber'],cookie)
                elif ofdProvider == 2:
                    receipt = receiptOfd2Read(param['id'],param['date'],param['fp'],cookie)
                if receipt != None:
                    receiptNotLoaded = False                
            receipts.append(receipt)
    return receipts

#testOFDRequest()

def addMeasureUnit(fdLinks,ofdProvider):
    #ofdDocuments = loadOfdDocs(fdLinks,1)
    ofdDocuments = loadOfdDocs(fdLinks,ofdProvider)
    #fd1 = int(input("Введите начальный ФД для коррекции: "))
    #fd2 = int(input("Введите конечный ФД для коррекции: "))
    fptr = IFptr("")
    version = fptr.version()

    fptr.setSingleSetting(IFptr.LIBFPTR_SETTING_MODEL, str(IFptr.LIBFPTR_MODEL_ATOL_AUTO))
    fptr.setSingleSetting(IFptr.LIBFPTR_SETTING_PORT, str(IFptr.LIBFPTR_PORT_USB))
    fptr.applySingleSettings()

    fptr.open()

    # ware1 = {"wareName": "AIME Гель д/душа с дозатором Delicate-уход 700мл",
    #         "price": 122.2,
    #         "quantity": 3,
    #         "sum": 366.6,
    #         "tax": 6}
    # ware2 = {"wareName": "AIME Крем-мыло д/интим.ухода с экст.жасмина 300 мл",
    #         "price": 78.6,
    #         "quantity": 2,
    #         "sum": 157.2,
    #         "tax": 6}
    # wares = [ware1,ware2]


    # payment1 = {"type": IFptr.LIBFPTR_PT_CASH, "sum": 500}
    # payment2 = {"type": IFptr.LIBFPTR_PT_ELECTRONICALLY, "sum": 23.8}
    # payments = [payment1,payment2]

    #receiptSell(fptr,wares,payments)
    #receiptSellCorrection(fptr,datetime.datetime(2024, 2, 10),wares,payments)
    #receiptSellReturnCorrection(fptr,datetime.datetime(2024, 2, 10),wares,payments)
    #lastFd = getLastFd(fptr)
    #fdNumber = 75
    for receipt in ofdDocuments:
        # fptr.setParam(IFptr.LIBFPTR_PARAM_FN_DATA_TYPE, IFptr.LIBFPTR_FNDT_DOCUMENT_BY_NUMBER)
        # fptr.setParam(IFptr.LIBFPTR_PARAM_DOCUMENT_NUMBER, fdNumber)
        # fptr.fnQueryData()
        # fdType = fptr.getParamInt(IFptr.LIBFPTR_PARAM_FN_DOCUMENT_TYPE)
        # if fdType in [IFptr.LIBFPTR_FN_DOC_RECEIPT]:
        #     receiptType = fptr.getParamInt(1054)
        #     receipt = receiptsRead(fptr,fdNumber)
        #     # Приход
        #     if receiptType == 1:
        #         receiptSellCorrection(fptr,receipt['fdDate'],receipt['wares'],receipt['payments'])
        #         pass
        #     # Возврат прихода
        #     elif receiptType == 2:
        #         receiptSellReturnCorrection(fptr,receipt['fdDate'],receipt['wares'],receipt['payments'])
        print("#" + str(receipt['fdNumber']))
        receiptType = receipt['receiptType']
        closeResult = -1
        while closeResult != 0:
            # Приход
            if receiptType == 1:
                closeResult = receiptSellCorrection(fptr,receipt['fdDate'],receipt['wares'],receipt['payments'])
            # Возврат прихода
            elif receiptType == 2:
                closeResult = receiptSellReturnCorrection(fptr,receipt['fdDate'],receipt['wares'],receipt['payments'])

    #receiptShowReadable(fptr,lastFd)

    fptr.close()

def changeTaxType(fdLinks,ofdProvider,newTaxType):
    ofdDocuments = loadOfdDocs(fdLinks,ofdProvider)
    fptr = IFptr("")
    version = fptr.version()

    fptr.setSingleSetting(IFptr.LIBFPTR_SETTING_MODEL, str(IFptr.LIBFPTR_MODEL_ATOL_AUTO))
    fptr.setSingleSetting(IFptr.LIBFPTR_SETTING_PORT, str(IFptr.LIBFPTR_PORT_USB))
    fptr.applySingleSettings()

    fptr.open()

    for receipt in ofdDocuments:
        print("#" + str(receipt['fdNumber']))
        receiptType = receipt['receiptType']
        closeResult = -1
        buyerPhoneOrAddress = receipt['buyerPhoneOrAddress']
        taxType = receipt['taxType']
        while closeResult != 0:
            #Обратная операция
            additionalTags = []
            additionalTags.append({"tagNumber": 1055,"tagValue": taxType})
            if buyerPhoneOrAddress != '':
                additionalTags.append({"tagNumber": 1008,"tagValue": buyerPhoneOrAddress})
            # Приход
            if receiptType == 1:
                closeResult = receiptSellReturnCorrection(fptr,receipt['fdDate'],receipt['wares'],receipt['payments'],additionalTags)
            # Возврат прихода
            elif receiptType == 2:
                closeResult = receiptSellCorrection(fptr,receipt['fdDate'],receipt['wares'],receipt['payments'],additionalTags)
            
            #Коррекция
            additionalTags = []
            additionalTags.append({"tagNumber": 1055,"tagValue": newTaxType})
            if buyerPhoneOrAddress != '':
                additionalTags.append({"tagNumber": 1008,"tagValue": buyerPhoneOrAddress})
            # Приход
            if receiptType == 1:
                closeResult = receiptSellCorrection(fptr,receipt['fdDate'],receipt['wares'],receipt['payments'],additionalTags)
            # Возврат прихода
            elif receiptType == 2:
                closeResult = receiptSellReturnCorrection(fptr,receipt['fdDate'],receipt['wares'],receipt['payments'],additionalTags)

    fptr.close()

fdLinks = "C:\\fdLinks.csv"
# ofdProvider = 2
# newTaxType = 32
# changeTaxType(fdLinks,ofdProvider,newTaxType)
ofdProvider = 2
addMeasureUnit(fdLinks,ofdProvider)