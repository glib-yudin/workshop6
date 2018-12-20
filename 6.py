import re
import plotly
from plotly import tools
import plotly.graph_objs as go

def get_date(line):
    raw_date, rest_line = re.split(r',', line, maxsplit=1)
    date = re.findall(r'\d{4}-\d{2}-\d{2}', raw_date)[0]
    return date, rest_line


def get_terminal(line):
    raw_terminal, rest_line = re.split(r',', line, maxsplit=1)
    terminal = re.findall(r'[\w\.\s{1}]+', raw_terminal)[0]
    # '          Terminal 1'
    return terminal.upper(), rest_line


def get_arrival(line):
    raw_arrival, rest_line = re.split(r',', line, maxsplit=1)
    raw_arrival = raw_arrival.upper()
    arrival = re.findall(r'ARRIVAL|DEPARTURE', raw_arrival)[0]
    return arrival, rest_line


try:
    dataset = {}
    current_line = 1

    with open('airport.csv') as file:
        header = file.readline()
        header = [word.strip().upper() for word in header.split(',')]

        for line in file:
            current_line += 1

            if not line:
                continue

            extract_date, tail = get_date(line)
            report_period, tail = get_date(tail)
            terminal, tail = get_terminal(tail)
            arr_dep, tail = get_arrival(tail)

            if terminal not in dataset:
                dataset[terminal] = {}
            if report_period not in dataset[terminal]:
                dataset[terminal][report_period] = {}
            if 'extract_date' not in dataset[terminal][report_period]:
                dataset[terminal][report_period]['extract_date'] = extract_date
            if 'A/D' not in dataset[terminal][report_period]:
                dataset[terminal][report_period]['A/D'] = {'arrival':0, 'departure':0}
            if arr_dep == 'ARRIVAL':
                dataset[terminal][report_period]['A/D']['arrival'] += 1
            elif arr_dep == 'DEPARTURE':
                dataset[terminal][report_period]['A/D']['departure'] += 1

        print(dataset)

# Приклад датасету:
# {'IMPERIAL TERMINAL': {
#     '2006-01-01': {
#         'extract_date': '2014-05-01',
#         'A/D': {
#             'arrival': 1,
#             'departure': 1
#             }
#         },
#     '2006-02-01': {...}
#     },
# 'TERMINAL 1': {
#     ...
# }
#-----------------------------------------------------------------------------
# Побудувати кругову діаграму: загальне співвідношення прильотів і вильотів.

    def arr_and_dep(dct, result):
        '''Обчислює загальну кількість прильотів і вильотів.

        dct(dict) -- словник, у якому ми зараз перебуваємо.
        result(dict) -- словник, у якому зберігається кількість прильотів і вильотів; створюється окремо.'''
        # якщо дійшли до потрібного словника -- додаємо дані до результату
        if 'A/D' in dct:
            result['arrival'] += dct['A/D']['arrival']
            result['departure'] += dct['A/D']['departure']
            return
        # інакше заходимо у глиб проміжних словників
        for key in dct:
            arr_and_dep(dct[key], result)
        # повертаємо словник з загальною кількість прильотів і вильотів
        return result


    arrivals = {'arrival':0, 'departure':0}
    arrivals = arr_and_dep(dataset, arrivals)
    fig1 = go.Pie(labels=tuple(arrivals.keys()), values=tuple(arrivals.values()), name='Arrivals/Departures')

#------------------------------------------------------------------------------------
# Побудувати стовпчикову діаграму: термінал і кількість рейсів в цьому терміналі (у порядку спадання).

    def most_crowded(dct, dset_terminals={}, curr_terminal=''):
        '''Знаходить інформацію про термінали та кількість рейсів, які вони обслужили.
        'Кількість рейсів' означає загальну кількість прильотів і вильотів разом.
        Потім буде сформовано топ-5 найбільш завантажених терміналів.

        dct(dict) -- словник, з яким зараз працюємо
        dset_terminals(dict) -- словник, ключі -- термінали, значення -- кількість рейсів на цьому терміналі.
        curr_terminal(str) -- назва терміналу, з якого витягуємо інформацію
        '''
        # якщо знайшли інформацію про вильоти:
        if 'A/D' in dct:
            dset_terminals[curr_terminal] += sum(dct['A/D'].values())
            return

        for key in dct:
            # якщо знайшли назву нового термінала (усі назви терміналів містять підрядок 'TERM')
            if key.find('TERM') != -1 and key not in dset_terminals:
                curr_terminal = key
                dset_terminals[curr_terminal] = 0

            # занурюємося глибше
            most_crowded(dct[key], dset_terminals, curr_terminal)

        return dset_terminals


    terminals_dict = most_crowded(dataset)
    # відсортовані values
    sorted_flights = sorted(terminals_dict.values())[::-1]
    # створюємо новий словник, у якому пари будуть відсортовані
    new_term_dict = {}
    # знаходимо термінал з найбільшою кількістю рейсів, додаємо у новий словник, продовжуємо...
    for flights in sorted_flights:
        for terminal in terminals_dict.keys():
            if terminals_dict[terminal] == flights:
                new_term_dict[terminal] = flights

    fig2 = go.Bar(x=tuple(new_term_dict.keys()), y=tuple(new_term_dict.values()), name='Terminals productivity')

#-----------------------------------------------------------
#    Побудувати графік: кількість рейсів за кожен місяць 2012-го року.

    def monthly_flights(dct, year, date_dict={} , curr_date='', pattern_year=''):
        '''Знаходить інформацію про кількість рейсів за вказану дату.
        'Кількість рейсів' означає загальну кількість прильотів і вильотів разом.

        dct(dict) -- словник, з яким зараз працюємо.
        year(int) -- рік, за який треба знайти інформацію.
        date_dict(dict) -- словник, ключі -- дати, значення -- кількість рейсів за цю дату.
        curr_date(str) -- поточна дата.
        pattern_year(str) -- допоміжний параметр для регулярних виразів; рік у типі str
        '''
        # якщо знайшли інформацію про вильоти потрібної дати(!) -- сумуємо кількість вильотів і прильотів
        if 'A/D' in dct and pattern_year in curr_date:
            date_dict[curr_date] += sum(dct['A/D'].values())
            return
        # якщо просто зайшли у найглибший словник -- виходимо з нього
        elif 'A/D' in dct:
            return

        # на початку роботи функції складаємо регулярний вираз для подальшого використання
        if not pattern_year:
            pattern_year = str(year)

        for key in dct:
            curr_date = key
            # якщо знайшли нову дату, та ще й потрібну нам
            if re.match(pattern_year, curr_date) and curr_date not in date_dict:
                # створюємо в date_dict нові ключ і значення
                date_dict[curr_date] = 0

            # занурюємося глибше
            monthly_flights(dct[key], year, date_dict, curr_date, pattern_year)

        return date_dict


    flights_2012 = monthly_flights(dataset, 2012)
    fig3 = go.Scatter(x=tuple(flights_2012.keys()), y=tuple(flights_2012.values()), name='Flights 2012')
    #-----------------------------------------------------

    plotly.offline.plot([fig1], filename='workshop6_1.html')
    plotly.offline.plot([fig2], filename='workshop6_2.html')
    plotly.offline.plot([fig3], filename='workshop6_3.html')
    # не бийте
    #-----------------------------------------------------
except ValueError as VE:
    print('ValueError at line', current_line)
except IOError as IO:
    print('IOError at line', current_line)