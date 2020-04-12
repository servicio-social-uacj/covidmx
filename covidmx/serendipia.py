import pandas as pd
from itertools import product
from unidecode import unidecode


class Serendipia:

    def __init__(
            self,
            date=None,
            kind=None,
            clean=True,
            add_search_date=True,
            date_format='%d-%m-%Y'):
        """
        Returns COVID19 data from serendipia.

        Parameters
        ----------
        date: str or list
            Dates to consider. If not present returns last found data.
        kind: str
            Kind of data. Allowed: 'positivos', 'sospechosos'. If not returns both.
        clean: boolean
            If data cleaning will be performed. Default True (recommended).
        add_search_date: boolean
            If add date to the DFs.
        date_format: str
            date format if needed
        """
        if not (
            isinstance(
                date,
                str) or isinstance(
                date,
                list) or date is None):
            raise ValueError('date must be string or list')

        if not (
            isinstance(
                kind,
                str) or isinstance(
                kind,
                list) or kind is None):
            raise ValueError('kind must be string or list')

        if not date:
            self.search_date = True
        else:
            self.search_date = False

        if isinstance(date, str) or date is None:
            self.date = [date]
        else:
            self.date = date

        if not kind:
            self.kind = ['positivos', 'sospechosos']

        if isinstance(kind, str):
            allowed_kinds = ('positivos', 'sospechosos')

            assert kind in allowed_kinds, 'Serendipia source only considers {}. Please use one of them.'.format(
                ', '.join(allowed_kinds))

            self.kind = [kind]

        self.clean = clean
        self.add_search_date = add_search_date
        self.date_format = date_format

    def get_data(self):

        print('Reading data')
        dfs = [
            self.read_data(
                dt, ki) for dt, ki in product(
                self.date, self.kind)]

        if self.clean:
            print('Cleaning data')
            dfs = [self.clean_data(df) for df in dfs]
            dfs = pd.concat(dfs, sort=True).reset_index(drop=True)

        return dfs

    def read_data(self, date, kind):

        if self.search_date:
            df, found_date = self.search_data(5, kind)

            if self.add_search_date:
                df['fecha_busqueda'] = found_date

            return df

        url = self.get_url(date, kind)

        try:
            df = pd.read_csv(url)

            if self.add_search_date:
                df['fecha_busqueda'] = date

            return df
        except BaseException:
            raise RuntimeError(
                f'Cannot read the data. Maybe theres no information for {kind} at {date}')

    def clean_data(self, df):

        df.columns = df.columns.str.lower().str.replace(
            ' |-', '_').str.replace('°', '').map(unidecode)
        df.columns = df.columns.str.replace(r'(?<=identificacion)(\w+)', '')
        # Removing Fuente row
        df = df[~df['n_caso'].str.contains('Fuente|Corte')]

        # converting to datetime format
        df.loc[:, 'fecha_busqueda'] = pd.to_datetime(
            df['fecha_busqueda'], format=self.date_format)
        df.loc[:, 'fecha_de_inicio_de_sintomas'] = pd.to_datetime(
            df['fecha_de_inicio_de_sintomas'], format='%d/%m/%Y')

        return df

    def search_data(self, max_times, kind):
        print(f'Searching last date available for {kind}...')

        search_dates = pd.date_range(
            end=pd.to_datetime('today'),
            periods=max_times)[
            ::-1]

        for date in search_dates:
            date_formatted = date.strftime(self.date_format)
            url = self.get_url(date_formatted, kind)
            try:
                df = pd.read_csv(url)
                print(f'Last date available: {date_formatted}')
                return df, date_formatted
            except BaseException:
                continue

        raise RuntimeError(f'No date found for {kind}')

    def get_url(self, date, kind):
        """
        Returns the url of serendipia.

        Parameters
        ----------
        date: str
            String date.
        kind: str
            String with kind of data. Allowed: 'positivos', 'sospechosos'
        """
        date_f = pd.to_datetime(date, format=self.date_format)
        year = date_f.strftime('%Y')
        month = date_f.strftime('%m')
        date_f = date_f.strftime('%Y.%m.%d')

        allowed_kinds = ('positivos', 'sospechosos')

        assert kind in allowed_kinds, 'Serendipia source only considers {}. Please use one of them.'.format(
            ', '.join(allowed_kinds))

        if kind == 'positivos':
            url = f'https://serendipia.digital/wp-content/uploads/{year}/{month}/Tabla_casos_{kind}_COVID-19_resultado_InDRE_{date_f}-Table-1.csv'
        else:
            url = f'https://serendipia.digital/wp-content/uploads/{year}/{month}/Tabla_casos_{kind}_COVID-19_{date_f}-Table-1.csv'

        return url