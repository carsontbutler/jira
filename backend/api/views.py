from django.shortcuts import render
from django.contrib.auth.models import User

from rest_framework import permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework import generics, status

from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView

from .serializers import *
from .models import *
from .serializers import *

class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        serializer = UserSerializerWithToken(self.user).data
        for k,v in serializer.items():
            data[k] = v
        return data

class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer

class RegisterUserView(generics.CreateAPIView):
  serializer_class = RegisterSerializer

#Organizations
class GetOrganizations(APIView):
    permission_classes = [IsAuthenticated]
    def get(self,request):
        user = request.user
        organizations = Organization.objects.filter(members__in=[user])
        data = OrganizationSerializer(organizations, many=True).data
        return Response(data, status=status.HTTP_200_OK)

class CreateOrganizationView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = CreateOrganizationSerializer

    def post(self, request):
        owner = request.user
        serializer = self.serializer_class(data=request.data)
        print(request)
        if serializer.is_valid():
            name = serializer.data.get('name')
            owner = request.user
            members_list = [owner]
            organization = Organization(name=name, owner=owner)
            organization.save() #I had to 
            organization.members.set(members_list)
            organization.save()
            return Response(CreateOrganizationSerializer(organization).data, status=status.HTTP_200_OK)
        print(serializer.errors)
        return Response(status=status.HTTP_400_BAD_REQUEST)

#Boards
class GetBoard(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        user = request.user
        organizations = Organization.objects.filter(members__in=[user])
        boards = Board.objects.filter(organization__in=[organizations][0])
        if boards.filter(id=pk).count() > 0:
            board = boards.filter(id=pk)[0]
            data = BoardSerializer(board).data
            return Response(data, status=status.HTTP_200_OK)
        return Response({'Bad Request':'Data unavailable'}, status=status.HTTP_404_NOT_FOUND)

class GetBoards(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        print(request.headers)
        user = request.user
        organizations = Organization.objects.filter(members__in=[user])
        boards = Board.objects.filter(organization__in=[org for org in organizations])

        data = {}
        data['organizations'] = []
        data['join_requests'] = []
        
        for i in range(len(organizations)):
            users = organizations[i].members.all()
            org_boards = boards.filter(organization=organizations[i])
            data['organizations'].append(OrganizationSerializer(organizations[i]).data)
            data['organizations'][i]['boards'] = BoardSerializer(org_boards, many=True).data
            data['organizations'][i]['users'] = UserSerializer(users, many=True).data

        owned_organizations = []
        for org in organizations:
            if org.owner == user:
                owned_organizations.append(org)
        requests = JoinRequest.objects.filter(organization__in=[org for org in owned_organizations])
        requests_data = JoinRequestSerializer(requests, many=True).data
        data['join_requests'] = requests_data
        for i in range(len(requests_data)):
            requester_username = UserSerializer(User.objects.get(id=int(requests_data[i]['requester']))).data
            data['join_requests'][i]['requester_info'] = requester_username
                   
        return Response(data, status=status.HTTP_200_OK)
      
class CreateBoardView(APIView):
    permission_classes=[IsAuthenticated]
    serializer_class = CreateBoardSerializer

    def post(self, request):
        print(request.data)
        user = request.user
        organizations = Organization.objects.filter(members__in=[user])
        #check if user belongs to the organization in the request data
        serializer = self.serializer_class(data=request.data)
        
        
        if serializer.is_valid():
            name = serializer.data.get('name')
            organization_id = serializer.data.get('organization')
            organization = organizations.get(id=organization_id)
            prefix = serializer.data.get('prefix')
            board = Board(name=name, organization=organization, prefix=prefix)
            board.save()
            return Response(CreateBoardSerializer(board).data, status=status.HTTP_200_OK)
        print(serializer.errors)
        return Response(status=status.HTTP_400_BAD_REQUEST)

class UpdateBoardView(generics.UpdateAPIView):
    permission_classes=[IsAuthenticated]
    queryset = Board.objects.all()
    serializer_class = BoardSerializer
    lookup_field = 'pk'

    def patch(self, request, *args, **kwargs):
        user = request.user
        organizations = Organization.objects.filter(members__in=[user]) #get user organizations
        instance = self.get_object() #get the board tied to the ticket
        organization = instance.organization
        if organization in organizations:
            print(request.data)
            serializer = self.get_serializer(instance, data=request.data, partial=True)
            if serializer.is_valid():
                print('VALID')
                serializer.save()
                return Response({'message': 'updated successfully'}, status=status.HTTP_200_OK)
            print('INVALID')
        return(Response({'message':'failed to update'}, status=status.HTTP_404_NOT_FOUND))

class DeleteBoardView(APIView):
    permission_classes=[IsAuthenticated]

    def delete(self, request, pk):
        user = request.user
        organizations = Organization.objects.filter(members__in=[user])
        Board = Board.objects.get(id=pk)
        board = board.board
        organization = board.organization
        if organization in organizations:
            board.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(status=status.HTTP_400_BAD_REQUEST)

#Columns
class CreateColumnView(APIView):
    permission_classes=[IsAuthenticated]
    serializer_class = CreateColumnSerializer

    def post(self, request):
        user = request.user
        organizations = Organization.objects.filter(members__in=[user])
        serializer = self.serializer_class(data=request.data)
        print(request.data)
        if serializer.is_valid():
            print('valid', request.data)
            board = Board.objects.get(id=request.data['board'])
            if board.organization in organizations:
                new_col = ColumnSerializer(data=request.data)
                if new_col.is_valid():
                    new_col.save()
                    return Response(status=status.HTTP_200_OK)
        return Response(status=status.HTTP_400_BAD_REQUEST)

class UpdateColumnView(generics.UpdateAPIView):
    permission_classes=[IsAuthenticated]
    serializer_class = ColumnSerializer
    queryset = Column.objects.all()
    lookup_field = 'pk'

    def put(self, request, *args, **kwargs):
        user = request.user
        organizations = Organization.objects.filter(members__in=[user])
        instance = self.get_object()
        this_board = instance.board
        this_org = this_board.organization
        if this_org in organizations:
            this_boards_columns = Column.objects.filter(board=this_board)
            column_count = len(this_boards_columns)
            max_position_value = column_count - 1
            if int(request.data['position']) > max_position_value:
                return(Response({'message':'Request exceeded max column position'}, status=status.HTTP_400_BAD_REQUEST))
            else:
                serializer = self.get_serializer(instance, data=request.data, partial=True)
                if serializer.is_valid():
                    serializer.save()
                    return Response({'message': 'updated successfully'}, status=status.HTTP_200_OK)
                print('INVALID')
                return(Response({'message':'failed to update'}, status=status.HTTP_400_BAD_REQUEST))
        return(Response({'message':'failed to update'}, status=status.HTTP_400_BAD_REQUEST))
            
class DeleteColumnView(APIView):
    permission_classes=[IsAuthenticated]

    def delete(self, request, pk):
        user = request.user
        organizations = Organization.objects.filter(members__in=[user])
        column = Column.objects.get(id=pk)
        board = column.board
        organization = board.organization
        if organization in organizations:
            column.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(status=status.HTTP_400_BAD_REQUEST)

#Tickets
class GetTickets(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        user = request.user
        organizations = Organization.objects.filter(members__in=[user])
        boards = Board.objects.filter(organization__in=[organizations][0])
        data = {}
        if boards.filter(id=pk).count() == 1:
            board = boards.filter(id=pk)[0]
            data['name'] = board.name
            data['prefix'] = board.prefix
            data['id'] = board.id
            data['columns'] = []
            columns = Column.objects.filter(board=board)
            tickets_query = Ticket.objects.filter(board=board)
            data['tickets'] = TicketSerializer(tickets_query, many=True).data
            for i in range(len(columns)):
                tickets_in_col = tickets_query.filter(column=columns[i])
                tickets_in_col_data = TicketSerializer(tickets_in_col, many=True).data
                data['columns'].append({'name':columns[i].name, 'id':columns[i].id, 'position': columns[i].position, 'tickets':tickets_in_col_data})
            return Response(data, status=status.HTTP_200_OK)
        return Response({'Bad Request':'Data unavailable'}, status=status.HTTP_404_NOT_FOUND)

class CreateTicketView(APIView):
    permission_classes=[IsAuthenticated]
    serializer_class = CreateTicketSerializer

    def post(self,request):
        user = request.user
        reporter = user.id
        organizations = Organization.objects.filter(members__in=[user])
        serializer = self.serializer_class(data=request.data)
        data = request.data
        data['reporter'] = reporter

        if serializer.is_valid():
            if len(Board.objects.filter(id=data['board'])) > 0:
                board = Board.objects.filter(id=data['board'])[0]
                organization = organizations.filter(id=board.id)[0]
                ticket = TicketSerializer(data=data)
                print(ticket)
                if ticket.is_valid():
                    ticket.save()
                    return Response(status=status.HTTP_200_OK)
                return Response(status=status.HTTP_403_FORBIDDEN)
        print(serializer.errors)
        return Response(status=status.HTTP_400_BAD_REQUEST)

class UpdateTicket(generics.UpdateAPIView):
    #! need to make sure it can only be updated if user belongs to the organization
    permission_classes = [IsAuthenticated]
    queryset = Ticket.objects.all()
    serializer_class = TicketSerializer
    lookup_field = 'pk'

    def patch(self, request, *args, **kwargs):
        user = request.user 
        organizations = Organization.objects.filter(members__in=[user])#get the organizations the user belongs to
        instance = self.get_object() #get the board tied to the ticket
        print('INSTANCE', instance)
        board = instance.board #get the organization tied to the board
        print('BOARD ', board)
        organization = board.organization
        if organization in organizations:
            print('yes')
        else:
            print('no')
        print(request.data)
        
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        if serializer.is_valid():
            print('VALID')
            serializer.save()
            return Response({'message': 'updated successfully'}, status=status.HTTP_200_OK)
        print('INVALID')
        return(Response({'message':'failed to update'}, status=status.HTTP_404_NOT_FOUND))
        
class DeleteTicketView(APIView):
    permission_classes=[IsAuthenticated]

    def delete(self, request, pk):
        user = request.user
        organizations = Organization.objects.filter(members__in=[user])
        ticket = Ticket.objects.get(id=pk)
        board = ticket.board
        organization = board.organization
        if organization in organizations:
            ticket.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(status=status.HTTP_400_BAD_REQUEST)


#JoinRequests
class SendJoinRequestView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = SendJoinRequestSerializer

    def post(self,request):
        data = request.data
        code = data['code']
        data['requester'] = request.user.id
        if len(Organization.objects.filter(code=code)) > 0:
            organization = Organization.objects.get(code=code)
            data['organization'] = organization.id
            if request.user not in organization.members.all():
                serializer = self.serializer_class(data=data)
                if serializer.is_valid():
                    serializer.save()
                    return Response({"message":"Request sent successfully."},status=status.HTTP_200_OK)
                return Response({"message":"Invalid data received."}, status=status.HTTP_400_BAD_REQUEST)
            return Response({"message":"User is already a member of that organization"}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"message":"Invalid data received."}, status=status.HTTP_400_BAD_REQUEST)



class ApproveJoinRequestView(APIView):
    permission_classes=[IsAuthenticated]

    def delete(self, request, pk):
        user = request.user
        organizations = Organization.objects.filter(members__in=[user])
        join_request = JoinRequest.objects.get(id=pk)
        organization = join_request.organization
        if organization in organizations and request.user == organization.owner:
            print(join_request)
            requester = join_request.requester
            print("adding ", requester, " to ", organization)
            organization.members.add(requester)
            join_request.delete()
            return Response({"message":"Join Request has been approved successfully."},status=status.HTTP_200_OK)
        return Response({"message":"Unable to process request. Try again later."},status=status.HTTP_400_BAD_REQUEST)

class DenyJoinRequestView(APIView):
    permission_classes=[IsAuthenticated]

    def delete(self, request, pk):
        user = request.user
        organizations = Organization.objects.filter(members__in=[user])
        join_request = JoinRequest.objects.get(id=pk)
        organization = join_request.organization
        if organization in organizations and request.user == organization.owner:
            join_request.delete()
            return Response({"message":"Join Request has been deleted successfully."},status=status.HTTP_200_OK)
        return Response({"message":"Unable to process request. Try again later."},status=status.HTTP_400_BAD_REQUEST)

#!not currently used
class GetJoinRequestsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self,request):
        user = request.user
        organizations = Organization.objects.filter(members__in=[user])
        owned_organizations = []
        for org in organizations:
            if org.owner == user:
                owned_organizations.append(org)
        requests = JoinRequest.objects.filter(organization__in=[org for org in owned_organizations])
        data = JoinRequestSerializer(requests, many=True).data
        return Response(data, status=status.HTTP_200_OK)