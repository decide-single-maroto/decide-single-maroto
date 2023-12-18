from rest_framework.views import APIView
from rest_framework.response import Response

class PostProcView(APIView):

    def identity(self, options):
        out = []

        for opt in options:
            out.append({
                **opt,
                'postproc': opt['votes'],
            });

        out.sort(key=lambda x: -x['postproc'])
        return Response(out)
    
    def dhondt(self, options):
        nSeats = int(self.request.data.get('seats'))
        seats={}

        results={}
        for opt in options: 
            if opt['option'] not in results: 
                results[opt['option']] = opt['votes']
            else: 
                results[opt['option']].append(opt['votes'])

        seats={}
        t_votes = results.copy()

        for key in results: seats[key]=0
        while sum(seats.values()) < nSeats:
            max_v= max(t_votes.values())
            next_seat=list(t_votes.keys())[list(t_votes.values()).index(max_v)]
            if next_seat in seats:
                seats[next_seat]+=1
            else:
                seats[next_seat]=1


            
            t_votes[next_seat]=results[next_seat]/(seats[next_seat]+1)
        return Response(seats)

    def post(self, request):
        """
         * type: IDENTITY | EQUALITY | WEIGHT
         * options: [
            {
             option: str,
             number: int,
             votes: int,
             ...extraparams
            }
           ]
        """

        t = request.data.get('type', 'IDENTITY')
        opts = request.data.get('options', [])

        if t == 'IDENTITY':
            return self.identity(opts)
        if t == 'DHONDT':
            return self.dhondt(opts)

        return Response({})
