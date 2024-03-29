from imp import SEARCH_ERROR
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from ..serializers import WordSerializer
from ..models import Word

class WordView(generics.ListAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = WordSerializer

    def get_queryset(self):
        # # # parameters
        search_word = self.request.query_params.get('search_word')
        wrapper_words = self.request.query_params.getlist('wrapper_words')
        # filter
        if search_word == None: 
            return Word.objects.none()
        
        search_word_objs = Word.objects.filter(text__icontains=search_word)
        queryset = []
        print(search_word_objs)
        count = 0 
        for search_word_obj in search_word_objs:
            search_word_obj.occurrences = search_word_obj.calculate_occurrences(wrapper_words)
            if search_word_obj.occurrences > 0:
                count += 1 
                queryset.append(search_word_obj)
            if count >= 5: 
                return queryset
        
        return queryset
        # search_word = self.request.query_params.get('search_word')
        # wrapper_words = self.request.query_params.getlist('wrapper_words')    
        # final_words = [search_word] + wrapper_words #All words 
        # queryset = []
        # if final_words == None: 
        #     return Word.objects.none()
        # for word in final_words: 
        #     search_word_objs = Word.objects.filter(text__icontains=word)
        # print(search_word_objs)
        # for search_word_obj in search_word_objs: 
        #     queryset.append(search_word_obj)
        # return queryset
        # queryset = []
        # for search_word_obj in search_word_objs:
        #     search_word_obj.occurrences = search_word_obj.calculate_occurrences(wrapper_words)
        #     if search_word_obj.occurrences > 0:
        #         queryset.append(search_word_obj)
