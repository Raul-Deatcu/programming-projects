from qgis.core import QgsProcessing
from qgis.core import QgsProcessingAlgorithm
from qgis.core import QgsProcessingMultiStepFeedback
from qgis.core import QgsProcessingParameterVectorLayer
from qgis.core import QgsProcessingParameterFile
from qgis.core import QgsProcessingParameterFolderDestination
from qgis.core import QgsProcessingParameterString
import processing
import os


class Model(QgsProcessingAlgorithm):

    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterVectorLayer('VectorInput', 'Select POIs', types=[QgsProcessing.TypeVectorAnyGeometry], defaultValue=None))
        self.addParameter(QgsProcessingParameterFolderDestination('Output', 'Select OUTPUT folder', defaultValue= None))
        self.addParameter(QgsProcessingParameterString('poiColumn', 'Write the column name for the POIs categories ', defaultValue= None, multiLine = False))
        self.addParameter(QgsProcessingParameterString('info', 'If you have NULL values in POIs category column, it will be omitted. You can also populate or delete them ', defaultValue= "DON'T WRITE ANYTHING HERE ", multiLine = False))
        

    def processAlgorithm(self, parameters, context, model_feedback):
        # Use a multi-step feedback, so that individual child algorithm progress reports are adjusted for the
        # overall progress through the model
        feedback = QgsProcessingMultiStepFeedback(3, model_feedback)
        results = {}
        outputs = {}

        # List unique values
        alg_params = {
            'FIELDS': parameters['poiColumn'],
            'INPUT': parameters['VectorInput']
        }
        lista = processing.run('qgis:listuniquevalues', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        artific = lista['UNIQUE_VALUES']
        artific2 = artific.split(";")
        if "NULL" in artific2:
            artific2.remove("NULL")


        feedback.setCurrentStep(1)
        if feedback.isCanceled():
            return {}
        
        decoy = 0
        for utilitate in artific2:
            # Extract by attribute
            alg_params = {
                'FIELD': parameters['poiColumn'],
                'INPUT': parameters['VectorInput'],
                'OPERATOR': 0,
                'VALUE': artific2[decoy],
                'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
            }
            outputs['ExtractByAttribute'] = processing.run('native:extractbyattribute', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

            feedback.setCurrentStep(2)
            if feedback.isCanceled():
                return {}

            output_path = parameters['Output']
            # Buffer
            alg_params = {
                'DISSOLVE': False,
                'DISTANCE': 0.001,
                'END_CAP_STYLE': 0,
                'INPUT': outputs['ExtractByAttribute']['OUTPUT'],
                'JOIN_STYLE': 0,
                'MITER_LIMIT': 2,
                'SEGMENTS': 5,
                'OUTPUT': os.path.join(output_path, artific2[decoy]+'.shp')
            }
            outputs['Buffer'] = processing.run('native:buffer', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
            results['Buff_kanal'] = outputs['Buffer']['OUTPUT']
            #return results
            decoy += 1
        return results

    def name(self):
        return 'model'

    def displayName(self):
        return 'View POIs in IQMaps '

    def group(self):
        return ''

    def groupId(self):
        return ''

    def createInstance(self):
        return Model()
