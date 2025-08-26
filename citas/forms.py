from django import forms
from .models import Cita

class CitaForm(forms.ModelForm):
    class Meta:
        model = Cita
        fields = ['nombre', 'telefono','correo', 'fecha', 'hora', 'edad', 'servicio']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        servicios_mayores = [
            "Consulta en línea","Psicoterapia","Terapia individual","Terapia familiar",
            "Terapia de pareja","TCC","Evaluación psicológica","Evaluaciones psicométricas",
            "Evaluaciones clínicas","Consulta psicológica online","Consulta de primera vez",
            "Visita Psicología","Terapia para adulto"
        ]
        servicios_menores = [
            "Psicoterapia para adolescentes","Psicoterapia infantil","Psicoterapia familiar",
            "Pruebas de ansiedad","Primera visita Psicología","Orientación para padres",
            "Intervención en crisis"
        ]

        if self.data.get('edad') == 'mayor':
            self.fields['servicio'].widget = forms.Select(choices=[(s,s) for s in servicios_mayores])
        elif self.data.get('edad') == 'menor':
            self.fields['servicio'].widget = forms.Select(choices=[(s,s) for s in servicios_menores])
