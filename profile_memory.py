import json
from typing import Any, Dict


class ProfileMemory:
    def __init__(self, path: str = "profile_structure.json") -> None:
        self.path = path

    def load(self) -> Dict[str, Any]:
        try:
            with open(self.path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"Profile file not found: {self.path}. Please run the profile preparer first.")
        # Normalize from common non-English schemas if needed
        if self._looks_french_schema(data):
            data = self._migrate_french_to_english(data)
            self.save(data)
        elif self._looks_spanish_schema(data):
            data = self._migrate_spanish_to_english(data)
            self.save(data)
        return data

    def save(self, profile: Dict[str, Any]) -> None:
        with open(self.path, 'w', encoding='utf-8') as f:
            json.dump(profile, f, ensure_ascii=False, indent=2)

    def _migrate_french_to_english(self, fr: Dict[str, Any]) -> Dict[str, Any]:
        identity = fr.get('identite', {})
        experiences_fr = fr.get('experiences', [])
        competences_fr = fr.get('competences', {})
        interests = fr.get('centres_interet')

        experiences_en = []
        for exp in experiences_fr:
            experiences_en.append({
                'company': exp.get('entreprise'),
                'location': exp.get('lieu'),
                'role': exp.get('poste'),
                'dates': exp.get('dates'),
                'missions': exp.get('missions', []),
            })

        profile_en = {
            'identity': {
                'name': identity.get('nom'),
                'title': identity.get('titre'),
            },
            'long_profile': fr.get('profil_long'),
            'experiences': experiences_en,
            'skills': {
                'technical': competences_fr.get('techniques', []),
                'methodological': competences_fr.get('methodologiques', []),
            },
            'education': fr.get('formation'),
            'languages': fr.get('langues', []),
            'interests': interests if interests is not None else [],
            # space for future adaptive memory
            'memory_notes': fr.get('memory_notes', {}),
        }
        return profile_en

    def _migrate_spanish_to_english(self, es: Dict[str, Any]) -> Dict[str, Any]:
        identidad = es.get('identidad', {})
        experiencias_es = es.get('experiencias', [])
        competencias_es = es.get('competencias', {})
        intereses = es.get('intereses')

        experiencias_en = []
        for exp in experiencias_es:
            experiencias_en.append({
                'company': exp.get('empresa'),
                'location': exp.get('lugar'),
                'role': exp.get('puesto'),
                'dates': exp.get('fechas'),
                'missions': exp.get('misiones', []),
            })

        profile_en = {
            'identity': {
                'name': identidad.get('nombre'),
                'title': identidad.get('titulo'),
            },
            'long_profile': es.get('perfil_largo'),
            'experiences': experiencias_en,
            'skills': {
                'technical': competencias_es.get('tecnicas', []),
                'methodological': competencias_es.get('metodologicas', []),
            },
            'education': es.get('formacion'),
            'languages': es.get('idiomas', []),
            'interests': intereses if intereses is not None else [],
            'memory_notes': es.get('memory_notes', {}),
        }
        return profile_en

    def _looks_french_schema(self, data: Dict[str, Any]) -> bool:
        return any(k in data for k in ['identite', 'profil_long', 'competences'])

    def _looks_spanish_schema(self, data: Dict[str, Any]) -> bool:
        return any(k in data for k in ['identidad', 'perfil_largo', 'competencias'])

    def record_adaptation_note(self, job_title: str, note: str) -> None:
        data = self.load()
        memory_notes = data.get('memory_notes', {})
        memory_notes[job_title] = note
        data['memory_notes'] = memory_notes
        self.save(data)


