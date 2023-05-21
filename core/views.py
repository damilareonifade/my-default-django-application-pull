from django.shortcuts import render


class ResponseCode():

    @classmethod
    def success(self, message:str ,data:dict):
        response = {"status":"200","message":message,"data":data}
        return response
        
    @classmethod
    def not_found(self,message:str,data:dict):
        response = {"status":"400","message":message,"data":data}
        return response