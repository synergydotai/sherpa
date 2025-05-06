"""
Google Sheets Client

Módulo para la integración con Google Sheets como fuente de datos para Sherpa.
"""

import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
import streamlit as st
from datetime import datetime
import json

class SheetsClient:
    def __init__(self, credentials_path, spreadsheet_id):
        """
        Inicializar el cliente de Google Sheets
        
        Args:
            credentials_path (str): Ruta al archivo JSON de credenciales de servicio
            spreadsheet_id (str): ID de la hoja de cálculo de Google Sheets
        """
        self.credentials_path = credentials_path
        self.spreadsheet_id = spreadsheet_id
        self.scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        self.client = None
        
    def get_raw_data(self, sheet_name, max_rows=6, max_cols=6):
        """
        Obtener datos directos de una hoja sin procesamiento
        
        Args:
            sheet_name (str): Nombre de la hoja
            max_rows (int): Número máximo de filas a obtener
            max_cols (int): Número máximo de columnas a obtener
            
        Returns:
            pd.DataFrame: Primeras filas y columnas de la hoja
        """
        if not self.client:
            if not self.connect():
                return pd.DataFrame()
        
        try:
            sheet = self.client.open_by_key(self.spreadsheet_id).worksheet(sheet_name)
            # Obtener todos los valores (como matriz)
            all_values = sheet.get_all_values()
            
            # Limitar filas y columnas
            limited_values = [row[:max_cols] for row in all_values[:max_rows+1]]  # +1 para incluir encabezados
            
            # Crear DataFrame
            if limited_values and len(limited_values) > 1:
                headers = limited_values[0]
                data = limited_values[1:max_rows+1]
                df = pd.DataFrame(data, columns=headers)
                return df
            else:
                return pd.DataFrame()
        except Exception as e:
            print(f"Error al obtener datos brutos de la hoja '{sheet_name}': {str(e)}")
            return pd.DataFrame()
    
    def connect(self):
        """Establecer conexión con Google Sheets API"""
        try:
            credentials = ServiceAccountCredentials.from_json_keyfile_name(self.credentials_path, self.scope)
            self.client = gspread.authorize(credentials)
            return True
        except Exception as e:
            st.error(f"Error al conectar con Google Sheets: {str(e)}")
            return False
    
    def get_sheet_as_df(self, sheet_name):
        """
        Obtener una hoja como DataFrame de pandas
        
        Args:
            sheet_name (str): Nombre de la hoja
            
        Returns:
            pd.DataFrame: DataFrame con los datos de la hoja
        """
        if not self.client:
            if not self.connect():
                return pd.DataFrame()
        
        try:
            sheet = self.client.open_by_key(self.spreadsheet_id).worksheet(sheet_name)
            data = sheet.get_all_records()
            return pd.DataFrame(data) if data else pd.DataFrame()
        except Exception as e:
            st.error(f"Error al obtener datos de la hoja '{sheet_name}': {str(e)}")
            return pd.DataFrame()
    
    def get_all_subnets(self):
        """
        Obtener todas las subnets con sus criterios y puntuaciones
        
        Returns:
            pd.DataFrame: DataFrame con información completa de subnets
        """
        # Obtener datos básicos de subnets
        subnets_df = self.get_sheet_as_df("subnets")
        
        if subnets_df.empty:
            return pd.DataFrame()
        
        # Obtener datos de criterios
        service_df = self.get_sheet_as_df("service_criteria")
        research_df = self.get_sheet_as_df("research_criteria")
        intelligence_df = self.get_sheet_as_df("intelligence_criteria")
        resource_df = self.get_sheet_as_df("resource_criteria")
        additional_df = self.get_sheet_as_df("additional_criteria")
        
        # Procesar cada subnet para calcular valores agregados
        for i, row in subnets_df.iterrows():
            subnet_id = row['id']
            
            # Filtrar criterios por subnet_id
            service_criteria = service_df[service_df['subnet_id'] == subnet_id]
            research_criteria = research_df[research_df['subnet_id'] == subnet_id]
            intelligence_criteria = intelligence_df[intelligence_df['subnet_id'] == subnet_id]
            resource_criteria = resource_df[resource_df['subnet_id'] == subnet_id]
            additional_criteria = additional_df[additional_df['subnet_id'] == subnet_id]
            
            # Convertir a diccionarios para almacenar en el DataFrame
            service_scores = {row['criterion_key']: row['score'] for _, row in service_criteria.iterrows()}
            research_scores = {row['criterion_key']: row['score'] for _, row in research_criteria.iterrows()}
            intelligence_scores = {row['criterion_key']: row['score'] for _, row in intelligence_criteria.iterrows()}
            resource_scores = {row['criterion_key']: row['score'] for _, row in resource_criteria.iterrows()}
            
            # Para criterios adicionales, necesitamos pesos
            additional_scores = {}
            additional_weights = {}
            for _, row in additional_criteria.iterrows():
                additional_scores[row['criterion_key']] = row['score']
                additional_weights[row['criterion_key']] = row['weight']
            
            # Guardar en el DataFrame como JSON strings (para compatible con la estructura existente)
            subnets_df.at[i, 'service_oriented_scores'] = json.dumps(service_scores)
            subnets_df.at[i, 'research_oriented_scores'] = json.dumps(research_scores)
            subnets_df.at[i, 'intelligence_oriented_scores'] = json.dumps(intelligence_scores)
            subnets_df.at[i, 'resource_oriented_scores'] = json.dumps(resource_scores)
            subnets_df.at[i, 'additional_criteria_scores'] = json.dumps({
                'scores': additional_scores,
                'weights': additional_weights
            })
            
            # Calcular promedios si no están ya en la hoja
            if 'service_avg' not in subnets_df.columns or pd.isna(row['service_avg']):
                service_avg = sum(service_scores.values()) / len(service_scores) if service_scores else 0
                subnets_df.at[i, 'service_avg'] = service_avg
                
            if 'research_avg' not in subnets_df.columns or pd.isna(row['research_avg']):
                research_avg = sum(research_scores.values()) / len(research_scores) if research_scores else 0
                subnets_df.at[i, 'research_avg'] = research_avg
                
            if 'intelligence_avg' not in subnets_df.columns or pd.isna(row['intelligence_avg']):
                intelligence_avg = sum(intelligence_scores.values()) / len(intelligence_scores) if intelligence_scores else 0
                subnets_df.at[i, 'intelligence_avg'] = intelligence_avg
                
            if 'resource_avg' not in subnets_df.columns or pd.isna(row['resource_avg']):
                resource_avg = sum(resource_scores.values()) / len(resource_scores) if resource_scores else 0
                subnets_df.at[i, 'resource_avg'] = resource_avg
        
        return subnets_df
    
    def get_criteria_definitions(self):
        """
        Obtener definiciones de criterios
        
        Returns:
            dict: Diccionario con definiciones de criterios por categoría
        """
        criteria_df = self.get_sheet_as_df("criteria_definitions")
        
        if criteria_df.empty:
            return {}
        
        # Organizar por categoría
        criteria_dict = {}
        
        for _, row in criteria_df.iterrows():
            category = row['category']
            key = row['key']
            
            if category not in criteria_dict:
                criteria_dict[category] = {}
            
            criteria_dict[category][key] = {
                "question": row['question'],
                "description": row['description']
            }
            
            # Añadir tipo para criterios adicionales
            if category == 'additional' and 'type' in row:
                criteria_dict[category][key]['type'] = row['type']
            
            # Añadir peso para criterios adicionales si está disponible
            if category == 'additional' and 'weight' in row:
                criteria_dict[category][key]['weight'] = row['weight']
        
        return criteria_dict