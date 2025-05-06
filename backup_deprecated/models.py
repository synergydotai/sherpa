"""
Modelos de datos para la aplicación Flask
"""
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json

db = SQLAlchemy()

# La clase User ha sido eliminada

class Subnet(db.Model):
    """Modelo para almacenar datos de subnets."""
    __tablename__ = 'subnets'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    uid = db.Column(db.String(100))
    description = db.Column(db.Text)
    service_research_score = db.Column(db.Float)
    intelligence_resource_score = db.Column(db.Float)
    total_score = db.Column(db.Float)
    tier = db.Column(db.String(20))
    service_oriented_scores = db.Column(db.Text)  # JSON string
    research_oriented_scores = db.Column(db.Text)  # JSON string
    intelligence_oriented_scores = db.Column(db.Text)  # JSON string
    resource_oriented_scores = db.Column(db.Text)  # JSON string
    additional_criteria_scores = db.Column(db.Text)  # JSON string
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    def to_dict(self):
        """Convertir objeto a diccionario para JSON API."""
        return {
            'id': self.id,
            'name': self.name,
            'uid': self.uid,
            'description': self.description,
            'service_research_score': self.service_research_score,
            'intelligence_resource_score': self.intelligence_resource_score,
            'total_score': self.total_score,
            'tier': self.tier,
            'service_oriented_scores': json.loads(self.service_oriented_scores) if self.service_oriented_scores else {},
            'research_oriented_scores': json.loads(self.research_oriented_scores) if self.research_oriented_scores else {},
            'intelligence_oriented_scores': json.loads(self.intelligence_oriented_scores) if self.intelligence_oriented_scores else {},
            'resource_oriented_scores': json.loads(self.resource_oriented_scores) if self.resource_oriented_scores else {},
            'additional_criteria_scores': json.loads(self.additional_criteria_scores) if self.additional_criteria_scores else {},
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }